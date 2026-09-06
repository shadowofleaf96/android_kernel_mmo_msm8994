# Talkman rear camera (Hill / SMIA++ / imx230)

Ident and qcamera HAL1 work. Live CSI does not.

The pixels HAL1 paints are the **CSID test generator**, not the sensor.
After TG-off, 4-lane irq is `0x20000dd` (uncorrectable ECC). CAMSS
(CSIPHY/CSID/CGC/LUT/lane_assign) was matched to live Windows Phone
viewfinder dumps; the remaining gap is the Sharp `0xEACA` / Sony IMX230
D-PHY stream.

Full handoff (what works, what was tried, what not to flash, dump
facts):

https://github.com/EpicLPer/Lumia950-Camera-Bringup

Early kernel bind PR (safe probe; text still says CCI NACK, which was
fixed later):

https://github.com/Android4Lumia950/android_kernel_mmo_msm8994/pull/4

Do not restart from bullhead IMX377, or from `sensor_power_up` at
kernel init (talkman bootloop). Keep `persist.camera.HAL3.enabled=0`.
