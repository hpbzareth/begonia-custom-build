# Redmi Note 8 Pro (Begonia / MT6785) Kernel Builder

![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/hpbzareth/begonia-custom-build/build.yml?branch=ksu-manual-hook&style=for-the-badge)
![Device](https://img.shields.io/badge/Device-Redmi%20Note%208%20Pro%20(Begonia)-orange?style=for-the-badge&logo=xiaomi)
![SoC](https://img.shields.io/badge/SoC-MediaTek%20Helio%20G90T%20(MT6785)-blue?style=for-the-badge)
![Kernel](https://img.shields.io/badge/Kernel-Linux%204.14.336-green?style=for-the-badge&logo=linux)
![Root](https://img.shields.io/badge/Root-KernelSU--Next%20v3.4.2-red?style=for-the-badge)
![SuSFS](https://img.shields.io/badge/Stealth-SuSFS%20v2.2-purple?style=for-the-badge)

Automated GitHub Actions builder for **Xiaomi Redmi Note 8 Pro (codename: `begonia` / `begoniain`)** based on [xiaomi-begonia-dev/android_kernel_xiaomi_mt6785](https://github.com/xiaomi-begonia-dev/android_kernel_xiaomi_mt6785). Built with **crDroid Clang 15** (r547379) and integrated with **KernelSU-Next v3.4.2** + **SuSFS v2.2.0**.

---

## 📱 Supported Devices & Variants

| Device | Codename | SoC | Branches Supported | Defconfig |
|---|---|---|:---:|---|
| **Redmi Note 8 Pro** | `begonia` / `begoniain` | MediaTek Helio G90T (MT6785) | `fourteen` (A14), `aosp-13`, `fifteen` (A15) | `begonia_user_defconfig` |

---

## 🛡️ Root & Stealth Frameworks

- **KernelSU-Next v3.4.2** (Legacy Non-GKI branch, UAPI v6 & UAPI v5 selectable).
- **SuSFS v2.2.0** (Anti-detection subsystem for hiding root, mount namespaces, open_redirect, kstat, cmdline, and uname spoofing).
- **APatch / FolkPatch Ready** (Vanilla variant with `CONFIG_KALLSYMS=y`, `CONFIG_KALLSYMS_ALL=y`, `CONFIG_KPROBES=y`).

---

## ⚡ Flashing Instructions

1. Download the AnyKernel3 flashable `.zip` and the matching Manager APK from **[Releases](../../releases)** or the **Actions** artifact tab.
2. Boot into **TWRP Recovery** or **OrangeFox Recovery**.
3. *(Recommended)* Perform a quick backup of your current **Boot** partition.
4. Tap **Install** → Select the downloaded `.zip` file → Swipe to flash.
5. Reboot to System.
6. Install the corresponding **KernelSU-Next Manager APK** (`KernelSU_Next_v3.4.2_uapi6-*.apk` or `uapi5-*.apk`).

---

## 🚀 Building via GitHub Actions

1. Go to the **Actions** tab on this repository.
2. Select **🔨 Build Begonia Kernel with KernelSU-Next & SuSFS**.
3. Click **Run workflow**:
   - **Kernel source branch:** `fourteen` (default), `aosp-13`, or `fifteen`.
   - **Root & SuSFS Variant:** `ksun_uapi6_susfs` (default), `ksun_uapi5_susfs`, `ksun_uapi6_nosusfs`, `ksun_uapi5_nosusfs`, or `vanilla`.
   - **Publish to GitHub Release:** `true` / `false`.
   - **Release Tag:** `Revision-1` (or custom tag).
4. Click **Run workflow** and monitor the build run!
