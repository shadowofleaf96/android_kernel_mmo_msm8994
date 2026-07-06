import glob
import re

files = glob.glob("arch/arm64/boot/dts/qcom/*.dtsi")

pattern = re.compile(
    r'\s*i2c@f9928000 \{\s*/\* BLSP1 QUP6 \*/\s*status = "ok";\s*pn547@28 \{.*?\};\s*\};\s*',
    re.DOTALL
)

replacement = """
&i2c_6 {
        status = "ok";
        pn547@28 {
                compatible = "nxp,pn547";
                reg = <0x28>;
                nxp,gpio_irq = <&msm_gpio 29 0x00>;
                nxp,gpio_ven = <&msm_gpio 30 0x00>;
                nxp,gpio_mode = <&msm_gpio 94 0x00>;


                qcom,clk-src = "BBCLK2";
                interrupt-parent = <&msm_gpio>;
                interrupts = <29 0>;
                interrupt-names = "nfc_irq";
                pinctrl-names = "nfc_active","nfc_suspend";
                pinctrl-0 = <&nfc_int_active &nfc_disable_active>;
                pinctrl-1 = <&nfc_int_suspend &nfc_disable_suspend>;
                qcom,clk-gpio = <&pm8994_gpios 10 0>;
                qcom,pwr-req-gpio = <&pm8994_gpios 7 0>;
                clocks = <&clock_rpm clk_bb_clk2_pin>;
                clock-names = "ref_clk";
        };
};
"""

for f in files:
    with open(f, 'r') as file:
        content = file.read()
    
    if "i2c@f9928000" in content and "nxp,pn547" in content:
        if "&i2c_6" not in content or "pn547@28" not in content[content.find("&i2c_6"):]:
            print(f"Fixing {f}...")
            # Extract the exact block
            match = pattern.search(content)
            if match:
                content = content[:match.start()] + content[match.end():]
                content = content.rstrip() + "\n" + replacement
                with open(f, 'w') as file:
                    file.write(content)
            else:
                print(f"Could not find exact block in {f}")

