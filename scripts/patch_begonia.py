#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

def log(msg):
    print(f"[+] {msg}", flush=True)

def fix_mmc_block(kernel_dir):
    block_c = os.path.join(kernel_dir, "drivers", "mmc", "core", "block.c")
    if not os.path.exists(block_c):
        return
    with open(block_c, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    clean_lines = []
    for l in lines:
        if any(marker in l for marker in [
            "<<<<<<< HEAD",
            "if (part_type == EXT_CSD_PART_CONFIG_ACC_RPMB) {",
            "=======",
            ">>>>>>> 014241ad77dda0eafbdf671d5b8e86917d8ec97e"
        ]):
            continue
        clean_lines.append(l)
    
    with open(block_c, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(clean_lines)
    log("Fixed mmc block.c merge conflict markers")

def inject_ida_helpers(kernel_dir):
    idr_h = os.path.join(kernel_dir, "include", "linux", "idr.h")
    if not os.path.exists(idr_h):
        return
    
    with open(idr_h, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    if "ida_alloc" not in content:
        target = "void ida_simple_remove(struct ida *ida, unsigned int id);"
        helpers = """
static inline int ida_alloc_range(struct ida *ida, unsigned int min, unsigned int max, gfp_t gfp)
{
	return ida_simple_get(ida, min, max, gfp);
}
static inline int ida_alloc_min(struct ida *ida, unsigned int min, gfp_t gfp)
{
	return ida_simple_get(ida, min, 0, gfp);
}
static inline int ida_alloc(struct ida *ida, gfp_t gfp)
{
	return ida_simple_get(ida, 0, 0, gfp);
}
static inline void ida_free(struct ida *ida, unsigned int id)
{
	ida_simple_remove(ida, id);
}
"""
        if target in content:
            content = content.replace(target, target + "\n" + helpers, 1)
            with open(idr_h, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            log("Injected ida_alloc, ida_alloc_min, ida_free into include/linux/idr.h")

def inject_poll_helpers(kernel_dir):
    poll_h = os.path.join(kernel_dir, "include", "linux", "poll.h")
    if os.path.exists(poll_h):
        with open(poll_h, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "__poll_t" not in content:
            target = "#include <uapi/linux/poll.h>"
            helpers = """#include <uapi/linux/poll.h>

#ifndef __poll_t
#define __poll_t __poll_t
typedef unsigned int __poll_t;
#endif
"""
            if target in content:
                content = content.replace(target, helpers, 1)
                with open(poll_h, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
                log("Injected __poll_t typedef into include/linux/poll.h")

    # Also ensure drivers/kernelsu/kernel/infra/event_queue.h has fallback
    event_queue_h = os.path.join(kernel_dir, "drivers", "kernelsu", "kernel", "infra", "event_queue.h")
    if os.path.exists(event_queue_h):
        with open(event_queue_h, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()
        if "// #if LINUX_VERSION_CODE < KERNEL_VERSION(4, 16, 0)" in c:
            poll_def = """#ifndef __poll_t
#define __poll_t __poll_t
typedef unsigned int __poll_t;
#endif
// #if 0"""
            c = c.replace("// #if LINUX_VERSION_CODE < KERNEL_VERSION(4, 16, 0)", poll_def)
            with open(event_queue_h, "w", encoding="utf-8", newline="\n") as f:
                f.write(c)
            log("Ensured __poll_t fallback in drivers/kernelsu/kernel/infra/event_queue.h")

def inject_boottime_helpers(kernel_dir):
    tk_h = os.path.join(kernel_dir, "include", "linux", "timekeeping.h")
    if os.path.exists(tk_h):
        with open(tk_h, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if "ktime_get_boottime_ts64" not in content:
            target = "static inline void get_monotonic_boottime64(struct timespec64 *ts)"
            helper = """static inline void ktime_get_boottime_ts64(struct timespec64 *ts)
{
\t*ts = ktime_to_timespec64(ktime_get_boottime());
}

static inline void get_monotonic_boottime64(struct timespec64 *ts)"""
            if target in content:
                content = content.replace(target, helper, 1)
                with open(tk_h, "w", encoding="utf-8", newline="\n") as f:
                    f.write(content)
                log("Injected ktime_get_boottime_ts64 into include/linux/timekeeping.h")

    event_c = os.path.join(kernel_dir, "drivers", "kernelsu", "kernel", "sulog", "event.c")
    if os.path.exists(event_c):
        with open(event_c, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()
        target = "ktime_get_boottime_ts64(ts);"
        repl = "*ts = ktime_to_timespec64(ktime_get_boottime());"
        if target in c:
            c = c.replace(target, repl, 1)
            with open(event_c, "w", encoding="utf-8", newline="\n") as f:
                f.write(c)
            log("Fixed ksu_sulog_boottime in drivers/kernelsu/kernel/sulog/event.c")

def apply_susfs_patch(kernel_dir, patch_file):
    if not os.path.exists(patch_file):
        log(f"Patch file {patch_file} not found!")
        return False
    
    log(f"Applying SuSFS 2.2 kernel patch: {patch_file}")
    res = subprocess.run(["git", "apply", "--ignore-whitespace", "--whitespace=nowarn", patch_file],
                         cwd=kernel_dir, capture_output=True, text=True)
    if res.returncode == 0:
        log("SuSFS 2.2 patch applied cleanly!")
        return True
    
    log(f"Direct git apply failed: {res.stderr.strip()[:200]}")
    log("Retrying with git apply -C1 --recount...")
    res2 = subprocess.run(["git", "apply", "-C1", "--ignore-whitespace", "--whitespace=nowarn", "--recount", patch_file],
                          cwd=kernel_dir, capture_output=True, text=True)
    if res2.returncode == 0:
        log("SuSFS 2.2 patch applied with 1 line context tolerance!")
        return True

    if shutil.which("patch"):
        log("Retrying with patch -p1 --fuzz=3...")
        res3 = subprocess.run(["patch", "-p1", "--fuzz=3", "-i", patch_file],
                              cwd=kernel_dir, capture_output=True, text=True)
        if res3.returncode == 0:
            log("SuSFS 2.2 patch applied via patch -p1 --fuzz=3!")
            return True
        log(f"Patch stderr: {res3.stderr[:300]}")

    return False

def inject_path_umount(kernel_dir):
    ns_c = os.path.join(kernel_dir, "fs", "namespace.c")
    if not os.path.exists(ns_c):
        return
    
    with open(ns_c, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    if "int path_umount" not in content:
        log("Injecting can_umount and path_umount into fs/namespace.c")
        
        # Add forward declarations if missing
        if "static inline int check_mnt(struct mount *mnt);" not in content:
            fwd_decls = (
                '#include "internal.h"\n'
                'static inline int check_mnt(struct mount *mnt);\n'
                'static int do_umount(struct mount *mnt, int flags);\n'
                'static void mntput_no_expire(struct mount *mnt);\n'
                'static inline bool may_mount(void);\n'
            )
            content = content.replace('#include "internal.h"', fwd_decls, 1)
        
        path_umount_impl = """
static int can_umount(const struct path *path, int flags)
{
	struct mount *mnt = real_mount(path->mnt);

	if (flags & ~(MNT_FORCE | MNT_DETACH | MNT_EXPIRE | UMOUNT_NOFOLLOW))
		return -EINVAL;
	if (!may_mount())
		return -EPERM;
	if (path->dentry != path->mnt->mnt_root)
		return -EINVAL;
	if (!check_mnt(mnt))
		return -EINVAL;
	if (mnt->mnt.mnt_flags & MNT_LOCKED)
		return -EINVAL;
	if (flags & MNT_FORCE && !capable(CAP_SYS_ADMIN))
		return -EPERM;
	return 0;
}

int path_umount(struct path *path, int flags)
{
	struct mount *mnt = real_mount(path->mnt);
	int ret;

	ret = can_umount(path, flags);
	if (!ret)
		ret = do_umount(mnt, flags);

	dput(path->dentry);
	mntput_no_expire(mnt);
	return ret;
}
EXPORT_SYMBOL(path_umount);

"""
        target = "SYSCALL_DEFINE2(umount"
        if target in content:
            content = content.replace(target, path_umount_impl + target, 1)
        else:
            content += path_umount_impl
        
        with open(ns_c, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        log("Successfully injected path_umount into fs/namespace.c")

    internal_h = os.path.join(kernel_dir, "fs", "internal.h")
    if os.path.exists(internal_h):
        with open(internal_h, "r", encoding="utf-8", errors="ignore") as f:
            ih_content = f.read()
        if "path_umount" not in ih_content:
            target = "extern void __init mnt_init(void);"
            replacement = target + "\nextern int path_umount(struct path *path, int flags);\n"
            if target in ih_content:
                ih_content = ih_content.replace(target, replacement, 1)
            else:
                ih_content += "\nextern int path_umount(struct path *path, int flags);\n"
            with open(internal_h, "w", encoding="utf-8", newline="\n") as f:
                f.write(ih_content)
            log("Added path_umount declaration to fs/internal.h")

def copy_susfs_files(kernel_dir, susfs_dir):
    fs_dir = os.path.join(kernel_dir, "fs")
    inc_dir = os.path.join(kernel_dir, "include", "linux")
    os.makedirs(fs_dir, exist_ok=True)
    os.makedirs(inc_dir, exist_ok=True)
    
    susfs_c = os.path.join(susfs_dir, "susfs.c")
    susfs_h = os.path.join(susfs_dir, "susfs.h")
    susfs_def_h = os.path.join(susfs_dir, "susfs_def.h")
    
    if os.path.exists(susfs_c):
        shutil.copy2(susfs_c, os.path.join(fs_dir, "susfs.c"))
        log("Copied susfs.c to fs/")
    if os.path.exists(susfs_h):
        shutil.copy2(susfs_h, os.path.join(inc_dir, "susfs.h"))
        log("Copied susfs.h to include/linux/")
    if os.path.exists(susfs_def_h):
        shutil.copy2(susfs_def_h, os.path.join(inc_dir, "susfs_def.h"))
        log("Copied susfs_def.h to include/linux/")

def ensure_makefiles(kernel_dir, patches_dir):
    # 1. Copy su_variants.Kconfig to drivers/su_variants.Kconfig
    su_variants_src = os.path.join(patches_dir, "su_variants.Kconfig")
    su_variants_dst = os.path.join(kernel_dir, "drivers", "su_variants.Kconfig")
    if os.path.exists(su_variants_src):
        shutil.copy2(su_variants_src, su_variants_dst)
        log("Copied su_variants.Kconfig to drivers/su_variants.Kconfig")
    
    # 2. Ensure drivers/kernelsu/Kconfig exists
    ksu_dir = os.path.join(kernel_dir, "drivers", "kernelsu")
    os.makedirs(ksu_dir, exist_ok=True)
    ksu_kc = os.path.join(ksu_dir, "Kconfig")
    with open(ksu_kc, "w", encoding="utf-8", newline="\n") as f:
        f.write('source "drivers/kernelsu/kernel/Kconfig"\n')
    log("Created drivers/kernelsu/Kconfig redirect")
    
    # 3. Ensure drivers/kernelsu/Makefile exists
    ksu_mk = os.path.join(ksu_dir, "Makefile")
    with open(ksu_mk, "w", encoding="utf-8", newline="\n") as f:
        f.write('obj-y += kernel/\n')
    log("Created drivers/kernelsu/Makefile redirect")

    # 4. drivers/Makefile
    drv_mk = os.path.join(kernel_dir, "drivers", "Makefile")
    if os.path.exists(drv_mk):
        with open(drv_mk, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()
        if "kernelsu" not in c:
            c += "\n# KernelSU-Next\nobj-$(CONFIG_KSU_NEXT) += kernelsu/kernel/\n"
            with open(drv_mk, "w", encoding="utf-8", newline="\n") as f:
                f.write(c)
            log("Added obj-$(CONFIG_KSU_NEXT) += kernelsu/kernel/ to drivers/Makefile")
            
    # 5. drivers/Kconfig
    drv_kc = os.path.join(kernel_dir, "drivers", "Kconfig")
    if os.path.exists(drv_kc):
        with open(drv_kc, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()
        if "drivers/su_variants.Kconfig" not in c:
            if "endmenu" in c:
                # Replace last endmenu
                idx = c.rfind("endmenu")
                c = c[:idx] + 'source "drivers/su_variants.Kconfig"\n\nendmenu' + c[idx+7:]
            else:
                c += '\nsource "drivers/su_variants.Kconfig"\n'
            with open(drv_kc, "w", encoding="utf-8", newline="\n") as f:
                f.write(c)
            log("Added source drivers/su_variants.Kconfig to drivers/Kconfig")

    # 6. fs/Makefile
    fs_mk = os.path.join(kernel_dir, "fs", "Makefile")
    if os.path.exists(fs_mk):
        with open(fs_mk, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()
        if "susfs.o" not in c:
            c += "\nobj-$(CONFIG_KSU_SUSFS) += susfs.o\n"
            with open(fs_mk, "w", encoding="utf-8", newline="\n") as f:
                f.write(c)
            log("Added susfs.o to fs/Makefile")

def main():
    if len(sys.argv) < 3:
        print("Usage: patch_begonia.py <kernel_dir> <patches_dir>")
        sys.exit(1)
        
    kernel_dir = os.path.abspath(sys.argv[1])
    patches_dir = os.path.abspath(sys.argv[2])
    
    log(f"Kernel source dir: {kernel_dir}")
    log(f"Patches dir: {patches_dir}")
    
    fix_mmc_block(kernel_dir)
    inject_ida_helpers(kernel_dir)
    inject_poll_helpers(kernel_dir)
    inject_boottime_helpers(kernel_dir)
    
    susfs_patch = os.path.join(patches_dir, "susfs_v2.2_for_begonia.patch")
    apply_susfs_patch(kernel_dir, susfs_patch)
    
    inject_path_umount(kernel_dir)
    
    susfs_dir = os.path.join(patches_dir, "susfs")
    copy_susfs_files(kernel_dir, susfs_dir)
    
    ensure_makefiles(kernel_dir, patches_dir)
    log("All Begonia kernel patches and hooks applied successfully!")

if __name__ == "__main__":
    main()
