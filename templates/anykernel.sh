### AnyKernel3 setup for Redmi Note 8 Pro (Begonia / MT6785)
properties() { '
kernel.string=Begonia Custom Kernel with KernelSU-Next & SuSFS
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=0
device.name1=begonia
device.name2=begoniain
supported.versions=
supported.patchlevels=
'; }

# shell variables
block=/dev/block/bootdevice/by-name/boot;
is_slot_device=0;
ramdisk_compression=auto;

## AnyKernel methods (DO NOT CHANGE)
. tools/ak3-core.sh;

## AnyKernel install
split_boot;
flash_boot;
## end install
