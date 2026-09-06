//===========================================================================
//                           <camera_resources.asl>
// DESCRIPTION
//   This file contans the resources needed by camera drivers.
//
//
//   Copyright (c) 2012-2014 by QUALCOMM Technologies Inc. All Rights Reserved.
//   Qualcomm Confidential and Proprietary
//
//===========================================================================


Scope(\_SB_.PEP0)
{
    // CAMERA
    Method(CPMD)
    {
        Return(CPCC)
    }

    // Exa-SoC Devices
    Method(CPMX)
    {
        Return (CPXC)
    }

    Name(CPCC, Package()
    {
        // Flash device
        Package()
        {
            "DEVICE",
            "\\_SB.FLSH",
            Package()
            {
                "COMPONENT",
                0x0, // Component 0
                Package()
                {
                    "FSTATE",
                    0x0, // F0 state
                },
                Package()
                {
                    "FSTATE",
                     0x1, //F1 state
                },
                Package()
                {
                    "PSTATE_SET",
                    0,
                    // Boost mode
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package()
                        {
                            "PMICVREGVOTE",
                            Package()
                            {
                                "PPP_RESOURCE_ID_BOOST_BYPASS1_B",
                                9, // Voltage Regulator Type, 9 = BOOST_BYPASS
                                3600000, // Voltage (uV) 3.6
                                1, // Software Enable
                                1, // Bypass Allowed
                                0, // Bypass Mode
                                0, // Pin Output Voltage
                            },
                        },
                    },
                    // Nominal max
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package()
                        {
                            "PMICVREGVOTE",
                            Package()
                            {
                                "PPP_RESOURCE_ID_BOOST_BYPASS1_B",
                                9, // Voltage Regulator Type, 9 = BOOST_BYPASS
                                3300000, // Voltage (uV) 3.3 V
                                1, // Software Enable
                                1, // Bypass Allowed
                                0, // Bypass Mode
                                0, // Pin Output Voltage
                            },
                        },

                    },
                    // off
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package()
                        {
                            "PMICVREGVOTE",
                            Package()
                            {
                                "PPP_RESOURCE_ID_BOOST_BYPASS1_B",
                                9, // Voltage Regulator Type, 9 = BOOST_BYPASS
                                0, // Voltage (uV) 0 V
                                0, // Software Disable
                                1, // Bypass Allowed
                                0, // Bypass Mode
                                0, // Pin Output Voltage
                            },
                        },
                    },
                },
            },
        },
        
        // JPEG Encoder device
        Package()
        {
            "DEVICE",
            "\\_SB.JPGE",
            Package()
            {
                "COMPONENT",
                0x0, // Component 0; JPEG 0 Encoder
                Package()
                {
                    "FSTATE",
                    0x0, // F0 State

                    // Footswitch
                    Package() { "FOOTSWITCH",        package() { "VDD_CAMSS_JPEG",        1 }},            
                    // AHB Clock - vote for 80Mhz
                    package() { "REQUIRED_RESOURCE", package() { 1, "/clk/mmnoc_ahb", 80000 }},
                    // Pstate for bandwidth. P2 state
                    Package() { "PSTATE_ADJUST",     package() { 1, 2 }},
                    
                    //                                   Req                                                         IB           AB
                    //                                   Type           Master                     Slave             Bytes/Sec    Bytes/Sec
                    //                               ----   -----------------------    ----------------------    ----------   ----------
                                                    // Action:       1 == ENABLE 3 == SET_FREQ   8 = Set frequency and enable
                                                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST                                
                                                    // Clock Name                 Action     Frequency            MatchType
                                                    // ----------                 ------     ----------           ----------
                    package() { "CLOCK", package() { "camss_top_ahb_clk",           1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_ahb_clk",               1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg0_clk",        1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_axi_clk",     1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_ahb_clk",     1,       000000000,             1,     }     },
                    // Pstate adjust for clock frequencies. P2 state
                    package() { "PSTATE_ADJUST", Package () { 0, 2 }},                    
                },
                // F1 state
                Package()
                {
                    "FSTATE",
                    0x1, // F1 State
                    package() { "CLOCK",  package() { "camss_jpeg_jpeg_ahb_clk",     2,       0,                     0,     }     },
                    package() { "CLOCK",  package() { "camss_jpeg_jpeg_axi_clk",     2,       0,                     0,     }     },
                    package() { "CLOCK",  package() { "camss_jpeg_jpeg0_clk",        2,       0,                     0,     }     },
                    package() { "CLOCK",  package() { "camss_ahb_clk",               2,       0,                     0,     }     },
                    package() { "CLOCK",  package() { "camss_top_ahb_clk",           2,       0,                     0,     }     },
                    package() { "PSTATE_ADJUST",     package() { 1, 3 }},
                    package() { "REQUIRED_RESOURCE", package() { 1, "/clk/mmnoc_ahb", 0}},
                    package() { "FOOTSWITCH",        package() { "VDD_CAMSS_JPEG",  2 }},
                },
                // P-state set 0: Clock frequency adjustments
                Package()
                {
                    "PSTATE_SET",
                    0,
					// Turbo mode
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package(){ "CLOCK", Package(){ "camss_jpeg_jpeg0_clk",              3,       465000000,       3,     }},
                    },
					// Nominal max
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package(){ "CLOCK", Package(){ "camss_jpeg_jpeg0_clk",              3,       320000000,       3,     }},
                    },
					// Standby mode
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package(){ "CLOCK", Package(){ "camss_jpeg_jpeg0_clk",              3,        75000000,       3,     }},
                    },
                },
                // P-state set 1: Bandwidth adjustments
                Package()
                {
                    "PSTATE_SET",
                    1,
					// Turbo mode
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     1395000000, 1395000000 } },
                    },
					// Nominal max
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     960000000, 960000000 } },
                    },
					// Standby mode
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     128000000, 128000000 } },
                    },
					// Off
                    Package()
                    {   
                        "PSTATE", 
                        3,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     000000000, 000000000 } },
                    },
                },
            },
			
            Package()
            {
                "COMPONENT",
                0x1, // Component 1; JPEG 1 Encoder
                Package()
                {
                    "FSTATE",
                    0x0, // F0 State

                    // Footswitch
                    Package() { "FOOTSWITCH",        package() { "VDD_CAMSS_JPEG",        1 }},            
                    // AHB Clock - vote for 80Mhz
                    package() { "REQUIRED_RESOURCE", package() { 1, "/clk/mmnoc_ahb", 80000 }},
                    // Pstate for bandwidth. P2 state
                    Package() { "PSTATE_ADJUST",     package() { 1, 2 }},
                    
                    //                               Req                                                           IB           AB
                    //                               Type           Master                     Slave             Bytes/Sec    Bytes/Sec
                    //                               ----   -----------------------    ----------------------    ----------   ----------
                                                    // Action:       1 == ENABLE 3 == SET_FREQ   8 = Set frequency and enable
                                                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST                                
                                                    // Clock Name                 Action     Frequency            MatchType
                                                    // ----------                 ------     ----------           ----------
                    package() { "CLOCK", package() { "camss_top_ahb_clk",           1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_ahb_clk",               1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_axi_clk",     1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_ahb_clk",     1,       000000000,             1,     }     },
                    // Pstate adjust for clock frequencies. P2 state
                    package() { "PSTATE_ADJUST", Package () { 0, 2 }},                    
                },
                // F1 state
                Package()
                {
                    "FSTATE",
                    0x1, // F1 State
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_ahb_clk",     2,       0,                     0,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_axi_clk",     2,       0,                     0,     }     },
                    package() { "CLOCK", package() { "camss_ahb_clk",               2,       0,                     0,     }     },
                    package() { "CLOCK", package() { "camss_top_ahb_clk",           2,       0,                     0,     }     },
                    package() { "PSTATE_ADJUST",     package() { 1, 3 }},
                    package() { "REQUIRED_RESOURCE", package() { 1, "/clk/mmnoc_ahb", 0}},
                    package() { "FOOTSWITCH",        package() { "VDD_CAMSS_JPEG",  2 }},
                },
                // P-state set 0: Clock frequency adjustments
                Package()
                {
                    "PSTATE_SET",
                    0,
                    // Turbo mode
                    Package()
                    { 
                        "PSTATE", 
                        0,
                    },
                    // Nominal max
                    Package()
                    { 
                        "PSTATE", 
                        1,
                    },
                    // Standby mode
                    Package()
                    { 
                        "PSTATE", 
                        2,
                    },
                },
                // P-state set 1: Bandwidth adjustments
                Package()
                {
                    "PSTATE_SET",
                    1,
                    // Turbo mode
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     1395000000, 1395000000 } },
                    },
                    // Nominal max
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     960000000, 960000000 } },
                    },
                    // Standby mode
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     128000000, 128000000 } },
                    },
                    // Off
                    Package()
                    {   
                        "PSTATE", 
                        3,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     000000000, 000000000 } },
                    },
                },
            },
            Package()
            {
                "COMPONENT",
                0x2, // Component 2; JPEG DMA. Note that this is normally indexed as JPEG core "3" in diagrams, but the ACPI entry index is 2 here
                Package()
                {
                    "FSTATE",
                    0x0, // F0 State

                    // Footswitch
                    Package() { "FOOTSWITCH",        package() { "VDD_CAMSS_JPEG",        1 }},            
                    // AHB Clock - vote for 80Mhz
                    package() { "REQUIRED_RESOURCE", package() { 1, "/clk/mmnoc_ahb", 80000 }},
                    // Pstate for bandwidth. P2 state
                    Package() { "PSTATE_ADJUST",     package() { 1, 2 }},
                    
                    //                               Req                                                           IB           AB
                    //                               Type           Master                     Slave             Bytes/Sec    Bytes/Sec
                    //                               ----   -----------------------    ----------------------    ----------   ----------
                                                    // Action:       1 == ENABLE 3 == SET_FREQ   8 = Set frequency and enable
                                                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST                                
                                                    // Clock Name                 Action     Frequency            MatchType
                                                    // ----------                 ------     ----------           ----------
                    package() { "CLOCK", package() { "camss_top_ahb_clk",           1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_ahb_clk",               1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_dma_clk",          1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_axi_clk",     1,       000000000,             1,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_ahb_clk",     1,       000000000,             1,     }     },
                    // Pstate adjust for clock frequencies. P2 state
                    package() { "PSTATE_ADJUST", Package () { 0, 2 }},                    
                },
                // F1 state
                Package()
                {
                    "FSTATE",
                    0x1, // F1 State
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_ahb_clk",     2,       0,                     0,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_jpeg_axi_clk",     2,       0,                     0,     }     },
                    package() { "CLOCK", package() { "camss_jpeg_dma_clk",          2,       0,                     0,     }     },
                    package() { "CLOCK", package() { "camss_ahb_clk",               2,       0,                     0,     }     },
                    package() { "CLOCK", package() { "camss_top_ahb_clk",           2,       0,                     0,     }     },
                    package() { "PSTATE_ADJUST",     package() { 1, 3 }},
                    package() { "REQUIRED_RESOURCE", package() { 1, "/clk/mmnoc_ahb", 0}},
                    package() { "FOOTSWITCH",        package() { "VDD_CAMSS_JPEG",  2 }},
                },
                // P-state set 0: Clock frequency adjustments
                Package()
                {
                    "PSTATE_SET",
                    0,
                    // Turbo mode
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package(){ "CLOCK", Package(){ "camss_jpeg_dma_clk",                3,       480000000,       3,     }},
                    },
                    // Nominal max
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package(){ "CLOCK", Package(){ "camss_jpeg_dma_clk",                3,       320000000,       3,     }},
                    },
                    // Standby mode
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package(){ "CLOCK", Package(){ "camss_jpeg_dma_clk",                3,        75000000,       3,     }},
                    },
                },
                // P-state set 1: Bandwidth adjustments
                Package()
                {
                    "PSTATE_SET",
                    1,
                    // Turbo mode
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     930000000, 930000000 } },
                    },
                    // Nominal max
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     640000000, 640000000 } },
                    },
                    // Standby mode
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     128000000, 128000000 } },
                    },
                    // Off
                    Package()
                    {   
                        "PSTATE", 
                        3,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_JPEG",          "ICBID_SLAVE_EBI1",     000000000, 000000000 } },
                    },
                },
            },
        },

        //Device CAMP Data
        Package()
        {
            "DEVICE",
            "\\_SB.CAMP",
            Package()
            {
                "COMPONENT",
                0x0, // Component 0.
                Package()
                {
                    "FSTATE",
                    0x0, // f0 state
                                        
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_TOP",           1    }},
										
                    //AHB Clock               
                    package(){"REQUIRED_RESOURCE", package(){ 1, "/clk/mmnoc_ahb" , 80000}},

                    // Action:       1 == ENABLE 2 == DISABLE 3 == SET_FREQ 8 == EN_SETFREQ
                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST
                    //                                  Clock Name           Action     Frequency        MatchType
                    //                                  ----------           ------     ----------       ----------
                    package(){ "CLOCK", package(){ "camss_top_ahb_clk",        1,         0,              1,     }},
                    package(){ "CLOCK", package(){ "camss_ahb_clk",            1,         0,              1,     }},//clock added for bring-up of IMX214
                    package(){ "CLOCK", package(){ "camss_cci_cci_ahb_clk",    1,         0,              1,     }},
                    package(){ "CLOCK", package(){ "camss_csi0_ahb_clk",       1,         0,              1,     }},
                    package(){ "CLOCK", package(){ "camss_cci_cci_clk",        1,         0,              1,     }},
                    Package(){"PSTATE_ADJUST", Package () { 0, 0 }},
                   
                    //                                   PIN   State     Func    Sel Direction PullDriveStrength
                    //Common for All CAM
                    package(){ "TLMMGPIO",  package(){     17,      1,     1,      1,     3,     0,},    }, // TLMMGPIO resource CAM_CCI_SDA0 2 mA
                    package(){ "TLMMGPIO",  package(){     18,      1,     1,      1,     3,     0,},    }, // TLMMGPIO resource CAM_CCI_SCL0
                    package(){ "TLMMGPIO",  package(){     19,      1,     1,      1,     3,     0,},    }, // TLMMGPIO resource CAM_CCI_SDA1
                    package(){ "TLMMGPIO",  package(){     20,      1,     1,      1,     3,     0,},    }, // TLMMGPIO resource CAM_CCI_SCL1

                    //CAM1 - Main(Rear)
                    package(){ "TLMMGPIO",  package(){     13,      1,     1,      1,     0,     2,},    }, // TLMMGPIO resource CAM_MCLK0 6mA     
                     
                    //CAM2 
                    //package(){ "TLMMGPIO",  package(){   14,      1,     1,      1,     0,     2,},    }, // TLMMGPIO resource CAM_MCLK1 6mA

                    //CAM3 - WebCam(Front)
                    package(){ "TLMMGPIO",  package(){     15,      1,     1,      1,     0,     2,},    }, // TLMMGPIO resource CAM_MCLK2 6mA
                    
                    //CAM4 - WebCam(Front)
                    package(){ "TLMMGPIO",  package(){     16,      1,     1,      1,     0,     2,},    }, // TLMMGPIO resource CAM_MCLK3 6mA
					
                    //CAM_OV4688_L_DVDD
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO3_A", // VREG ID
                            1,         // Voltage Regulator type = LDO
                            1200000,   // Voltage is in micro volts on 89 // No change
                            140000,    // Peak current in microamps //OV4688 spec mentions 120mA as typical, peak TBD. Ask OV/ Liteon?
                            1,         // force enable from software
                            0,         // disable pin control enable
                            1,         // power mode - Normal Power Mode
                            0,         // power mode pin control - disable
                            0,         // bypass mode allowed
                            0,         // head room voltage
                        },
                    },
                    // CAM_IMX214_L_DVDD
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO27_A", // VREG ID
                            1,         // Voltage Regulator type = LDO
                            1050000,    // Voltage is in micro volts // 1.05V
                            333000,    // Peak current in microamps // HDR mode has a max of 333mA
                            1,         // force enable from software
                            0,         // disable pin control enable
                            1,         // power mode - Normal Power Mode
                            0,         // power mode pin control - disable
                            0,         // bypass mode allowed
                            0,         // head room voltage
                        },
                    },
                    //CAM_IMX214_L_AF_VDD
		    //CAM_OV4688_L_ACTVDD
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO23_A", // VREG ID
                            1,          // Voltage Regulator type = LDO
                            2800000,    // Voltage is in micro volts on 89 // RFC range is 2.6V to 3.6V, FFC range is 2.3V to 3.6V
                            474000,     // Peak current in microamps // Additive (350mA for RFC + 120mA for FFC), (350mA is additive of AF + OIS) 
                            1,          // force enable from software
                            0,          // disable pin control enable
                            1,          // power mode - Normal Power Mode
                            0,          // power mode pin control - disable
                            0,          // bypass mode allowed
                            0,          // head room voltage
                        },
                    },
		    //CAM_OV4688_L_AVDD
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO29_A", // VREG ID
                            1,          // Voltage Regulator type = LDO
                            2800000,    // Voltage is in micro volts on 8 //2.6V to 3.0 as per spec
                            100000,     // Peak current in microamps //typical is 40mA for FFC
                            1,          // force enable from software
                            0,          // disable pin control enable
                            1,          // power mode - Normal Power Mode
                            0,          // power mode pin control - disable
                            0,          // bypass mode allowed
                            0,          // head room voltage
                        },
                    },
                    //CAM_OV4688_L_AVDD
                    //CAM_OV7750_LEFT_2P85 //Gesture 3D camera
                    //CAM_OV7750_RIGHT_2P85
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO17_A", // VREG ID
                            1,          // Voltage Regulator type = LDO
                            2700000,    // Voltage is in micro volts on 89 //spec has 2.8V typical for FFC and OV7750 cameras.
                            111000,     // Peak current in microamps       // additive for FFC and gesture cameras (51mA + 30mA + 30mA)
                            1,          // force enable from software
                            0,          // disable pin control enable
                            1,          // power mode - Normal Power Mode
                            0,          // power mode pin control - disable
                            0,          // bypass mode allowed
                            0,          // head room voltage
                        },
                    },
                    //LVS     CAM_IMX214_L_DOVDD
                    //        CAM_OV4688_L_DOVDD
                    //CAM_OV7750_LEFT_VDD_1P8 //Gesture 3D camera
                    //CAM_OV7750_RIGHT_VDD_1P8 
                    package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        package()
                        {
                            "PPP_RESOURCE_ID_LVS1_A",
                            4,          // TYPE of VREG = LVS
                            1800000,    // 1.8V
                            109000,     // Peak current in microamps (Additive RFC (6mA) + FFC (3mA) + Gesture cams (50mA + 50mA)) RFC spec says Ipeak 4mA, 
                            1,          // Force enable from s/w
                            0,          // disable pin control
                        },
                    },
                    package()
                    {
                        "DELAY", // Clock resource
                        package()
                        {
                            10,  // 10 Milsec delay
                        }
                    },
                },
                Package()
                {
                    "FSTATE",
                    0x1, // f1 state
                    package(){ "TLMMGPIO",  package(){     16,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_MCLK4
                    package(){ "TLMMGPIO",  package(){     15,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_MCLK3
                    package(){ "TLMMGPIO",  package(){     14,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_MCLK2
                    package(){ "TLMMGPIO",  package(){     13,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_MCLK0   
                    package(){ "TLMMGPIO",  package(){     20,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_CCI_SCL1 
                    package(){ "TLMMGPIO",  package(){     19,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_CCI_SDA1
                    package(){ "TLMMGPIO",  package(){     18,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_CCI_SCL0
                    package(){ "TLMMGPIO",  package(){     17,      0,     0,      0,     1,     0,},    }, // TLMMGPIO resource CAM_CCI_SDA0

                    package(){ "CLOCK", package(){ "camss_cci_cci_clk",             2,          0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi0_ahb_clk",            2,          0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_cci_cci_ahb_clk",         2,          0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_top_ahb_clk",             2,          0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_ahb_clk",                 2,          0,              1,     }},
                    package(){ "REQUIRED_RESOURCE", package(){ 1, "/clk/mmnoc_ahb", 0}},
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_TOP",           2}},
                    
                    //LVS     CAM_IMX214_L_DOVDD
                    //        CAM_OV4688_L_DOVDD
                    package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        package()
                        {
                            "PPP_RESOURCE_ID_LVS1_A",
                            4,      // TYPE of VREG = LVS
                            0,      // 1.8V
                            0,      // Peak current in microamps
                            0,      // Force enable from s/w
                            0,      // disable pin control
                        },
                    },
                    //CAM_OV4688_L_AVDD
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO17_A", // VREG ID
                            1,          // Voltage Regulator type = LDO
                            0,          // Voltage is in micro volts on 89
                            0,          // Peak current in microamps
                            0,          // force enable from software
                            0,          // disable pin control enable
                            0,          // power mode - LPM
                            0,          // power mode pin control - disable
                            0,          // bypass mode allowed
                            0,          // head room voltage
                        },
                    },
                    //CAM_OV4688_L_AVDD
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO29_A", // VREG ID
                            1,          // Voltage Regulator type = LDO
                            0,          // Voltage is in micro volts on 89
                            0,          // Peak current in microamps
                            0,          // force enable from software
                            0,          // disable pin control enable
                            0,          // power mode - LPM
                            0,          // power mode pin control - disable
                            0,          // bypass mode allowed
                            0,          // head room voltage
                        },
                    },
                    //CAM_IMX214_L_AF_VDD
                    //CAM_OV4688_L_ACTVDD
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO23_A", // VREG ID
                            1,          // Voltage Regulator type = LDO
                            0,          // Voltage is in micro volts on 89
                            0,          // Peak current in microamps
                            0,          // force enable from software
                            0,          // disable pin control enable
                            0,          // power mode - LPM
                            0,      // power mode pin control - disable
                            0,      // bypass mode allowed
                            0,      // head room voltage
                        },
                    },
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO27_A", // VREG ID
                            1,      // Voltage Regulator type = LDO
                            0,      // Voltage is in micro volts
                            0,      // Peak current in microamps
                            0,      // force enable from software
                            0,      // disable pin control enable
                            0,      // power mode - LPM
                            0,      // power mode pin control - disable
                            0,      // bypass mode allowed
                            0,      // head room voltage
                        },
                    },
                    Package()
                    {
                        "PMICVREGVOTE", // PMICVREGVOTE resource
                        Package()
                        {
                            "PPP_RESOURCE_ID_LDO3_A", // VREG ID
                            1,          // Voltage Regulator type = LDO
                            0,          // Voltage is in micro volts on 89
                            0,          // Peak current in microamps
                            0,          // force enable from software
                            0,          // disable pin control enable
                            0,          // power mode - LPM
                            0,          // power mode pin control - disable
                            0,          // bypass mode allowed
                            0,          // head room voltage
                        },
                    },
                },

                Package()
                {
                        "PSTATE_SET",
                        0,
                        // used for I2C bus speed of 100 / 400 khz
                        Package()
                        { 
                            "PSTATE",    
                            0,
                            package(){ "CLOCK", package(){ "camss_cci_cci_clk", 3, 19200000, 3, }},
                        },
                        // used for I2C bus speed of 1 Mhz
                        Package()
                        { 
                            "PSTATE", 
                            1,        
                            package(){ "CLOCK", package(){ "camss_cci_cci_clk", 3, 37200000, 3, }},
                        },
                },
            },
        },

        //Device VFE0 Data
        Package()
        {
            "DEVICE",
            "\\_SB.VFE0",
            Package()
            {
                "COMPONENT",
                0x0, // Component 0.  //VFE 0 component
                Package()
                {
                    "FSTATE",
                    0x0, // F0 state
          
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_VFE",           1    }},
                    Package(){"PSTATE_ADJUST", Package () { 1, 3 }},
                   
                    // Action:       1 == ENABLE 2 == DISABLE 3 == SET_FREQ 8 == EN_SETFREQ
                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST
                    //                                  Clock Name                 Action     Frequency       MatchType
                    //                                  ---------                  ------     ----------      ----------
                    package(){ "CLOCK", package(){ "camss_vfe_vfe0_clk",              1,       0,       1,     }}, 
                    Package(){"PSTATE_ADJUST", Package () { 0, 5 }},
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_axi_clk",           1,       0,               1,     }}, 
                    package(){ "CLOCK", package(){ "camss_top_ahb_clk",               1,       0,               1,     }}, 
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_ahb_clk",           1,       0,               1,     }},
                    package(){ "CLOCK", package(){ "camss_ahb_clk",                   1,       0,               1,     }}, 
                },
                Package()
                {
                    "FSTATE",
                    0x1, // F1 state
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_ahb_clk",              2,       0,                0,     }},
                    package(){ "CLOCK", package(){ "camss_top_ahb_clk",                  2,       0,                0,     }},
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_axi_clk",              2,       0,                0,     }},
                    package(){ "CLOCK", package(){ "camss_vfe_vfe0_clk",                 2,       0,                0,     }},
                    package(){ "CLOCK", package(){ "camss_ahb_clk",                      2,       0,                0,     }},
                    Package(){"PSTATE_ADJUST", Package () { 1, 13 }},
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_VFE",           2    }},
                },
                Package()
                {
                    "PSTATE_SET",
                    0,
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe0_clk",              3,       600000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe0_clk",              3,       480000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        4,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe0_clk",              3,       320000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        5,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe0_clk",              3,       200000000,       3,     }},
                    },
                    Package()
                    {  
                        "PSTATE", 
                        6,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe0_clk",              3,       100000000,       3,     }},
                    },
                    Package()
                    {   
                        "PSTATE", 
                        7,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe0_clk",              3,       80000000,        3,     }},
                    },
                },
                Package()
                {
                    "PSTATE_SET",
                    1,
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     4000000000,   4000000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     3600000000,   3600000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     3300000000,   3300000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        3,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     3000000000,   3000000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        4,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     2700000000,   2700000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        5,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     2400000000,   2400000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        6,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     2100000000,   2100000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        7,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     1800000000,   1800000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        8,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     1500000000,   1500000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        9,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     1200000000,   1200000000 } },
                    },
                    Package()
                    {
                        "PSTATE", 
                        10,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     900000000,   900000000 } },
                    },
                    Package()
                    {
                        "PSTATE", 
                        11,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     600000000,   600000000 } },
                    },
                    Package()
                    {
                        "PSTATE", 
                        12,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     300000000,   300000000 } },
                    },
                    Package()
                    {  
                        "PSTATE", 
                        13,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     0,   0 } },
                    },
                },
            },
            Package()
            {
                "COMPONENT",
                0x1, // Component 1.  //VFE 1 component
                Package()
                {
                    "FSTATE",
                    0x0, // F0 state
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_VFE",           1    }},
                    Package(){"PSTATE_ADJUST", Package () { 1, 3 }},
                    // Action:       1 == ENABLE 2 == DISABLE 3 == SET_FREQ 8 == EN_SETFREQ
                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST
                    //                                  Clock Name                 Action     Frequency       MatchType
                    //                                  ---------                  ------     ----------      ----------
                    package(){ "CLOCK", package(){ "camss_vfe_vfe1_clk",              1,       0,       1,     }}, 
                    Package(){"PSTATE_ADJUST", Package () { 0, 5 }},
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_axi_clk",           1,       0,               1,     }}, 
                    package(){ "CLOCK", package(){ "camss_top_ahb_clk",               1,       0,               1,     }}, 
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_ahb_clk",           1,       0,               1,     }}, 
                },
                Package()
                {
                    "FSTATE",
                    0x1, // F1 state
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_ahb_clk",           2,       0,       0,     }},
                    package(){ "CLOCK", package(){ "camss_top_ahb_clk",               2,       0,       0,     }},
                    package(){ "CLOCK", package(){ "camss_vfe_vfe_axi_clk",           2,       0,       0,     }},
                    package(){ "CLOCK", package(){ "camss_vfe_vfe1_clk",              2,       0,       0,     }},
                    Package(){"PSTATE_ADJUST", Package () { 1, 13 }},
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_VFE",           2    }},          

                },
                Package()
                {
                    "PSTATE_SET",
                    0,
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe1_clk",              3,       600000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe1_clk",              3,       480000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        4,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe1_clk",              3,       320000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        5,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe1_clk",              3,       200000000,       3,     }},
                    },
                    Package()
                    {  
                        "PSTATE", 
                        6,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe1_clk",              3,       100000000,       3,     }},
                    },
                    Package()
                    {   
                        "PSTATE", 
                        7,
                        Package(){ "CLOCK", Package(){ "camss_vfe_vfe1_clk",              3,       80000000,        3,     }},
                    },
                },
                Package()
                {
                    "PSTATE_SET",
                    1,
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     4000000000,   4000000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     3600000000,   3600000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     3300000000,   3300000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        3,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     3000000000,   3000000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        4,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     2700000000,   2700000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        5,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     2400000000,   2400000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        6,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     2100000000,   2100000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        7,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     1800000000,   1800000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        8,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     1500000000,   1500000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        9,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     1200000000,   1200000000 } },
                    },
                    Package()
                    {
                        "PSTATE", 
                        10,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     900000000,   900000000 } },
                    },
                    Package()
                    {
                        "PSTATE", 
                        11,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     600000000,   600000000 } },
                    },
                    Package()
                    {
                        "PSTATE", 
                        12,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     300000000,   300000000 } },
                    },
                    Package()
                    {  
                        "PSTATE", 
                        13,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     0,   0 } },
                    },
                },
            },
            Package()
            {
                "COMPONENT",
                0x2, // Component 2.  //CPP component
                Package()
                {
                    "FSTATE",
                    0x0, // F0 state
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_CPP",           1    }},
                    Package(){"PSTATE_ADJUST", Package () { 1, 4 }},
                    // CPP clocks
                    package(){ "CLOCK", package(){ "camss_vfe_cpp_clk",                1,          0,                1,     }},
                    Package(){"PSTATE_ADJUST", Package () { 0, 2 }},
                    package(){ "CLOCK", package(){ "camss_vfe_cpp_axi_clk",            1,          0,                1,     }}, 
                    package(){ "CLOCK", package(){ "camss_ahb_clk",                    1,          0,                1,     }}, 
                    package(){ "CLOCK", package(){ "camss_vfe_cpp_ahb_clk",            1,          0,                1,     }},
                    //RESETCLOCK_ASSERT for camss_micro_ahb_clk
                    package(){ "CLOCK", package(){ "camss_micro_ahb_clk",              10,         0,                1,     }},
                    //RESETCLOCK_DEASSERT for camss_micro_ahb_clk
                    package(){ "CLOCK", package(){ "camss_micro_ahb_clk",              11,         0,                1,     }},
                    //now enable camss_micro_ahb_clk
                    package(){ "CLOCK", package(){ "camss_micro_ahb_clk",              1,          0,                1,     }},
                },
                Package()
                {
                    "FSTATE",
                    0x1, // F1 state
                    package(){ "CLOCK", package(){ "camss_micro_ahb_clk",              2,         0,                0,     }},
                    package(){ "CLOCK", package(){ "camss_vfe_cpp_ahb_clk",            2,         0,                0,     }},
                    package(){ "CLOCK", package(){ "camss_vfe_cpp_clk",                2,         0,                0,     }},
                    package(){ "CLOCK", package(){ "camss_ahb_clk",                    2,         0,                0,     }}, 
                    package(){ "CLOCK", package(){ "camss_vfe_cpp_axi_clk",            2,         0,                1,     }}, 
                    Package(){"PSTATE_ADJUST", Package () { 1, 8 }},                    
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_CPP",           2    }},					
                },
                Package()
                {
                    "PSTATE_SET",
                    0,
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package(){ "CLOCK", Package(){ "camss_vfe_cpp_clk",              3,       620000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package(){ "CLOCK", Package(){ "camss_vfe_cpp_clk",              3,       600000000,       3,     }},
                    },
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package(){ "CLOCK", Package(){ "camss_vfe_cpp_clk",              3,       465000000,       3,     }},
                    },
               },
                Package()
                {
                    "PSTATE_SET",
                    1,
                    Package()
                    { 
                        "PSTATE", 
                        0,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     3400000000,   3400000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        1,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     2400000000,   2400000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        2,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     1200000000,   1200000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        3,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     800000000,   800000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        4,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     200000000,   200000000 } },
                    },
                    Package()
                    { 
                        "PSTATE", 
                        5,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     120000000,   120000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        6,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     60000000,   60000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        7,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     30000000,   30000000 } },
                    },
                    Package()
                    {   
                        "PSTATE", 
                        8,
                        Package() { "BUSARB", Package() { 3,    "ICBID_MASTER_VFE",          "ICBID_SLAVE_EBI1",     0,           0 } },             
                    },
               },

           },
            Package()
            {
                "COMPONENT",
                0x3, // Component 3.  //FD component
                Package()
                {
                    "FSTATE",
                    0x0, // F0 state
		            Package(){ "CLOCK", package(){ "fd_ahb_clk",                       1,          0,                1,     }},
		            Package(){ "CLOCK", package(){ "fd_axi_clk",                       1,          0,                1,     }}, 
	                Package(){ "CLOCK", package(){ "fd_core_uar_clk",                  1,          0,                1,     }}, 
                    Package(){ "CLOCK", Package(){ "fd_core_clk",                      8,       266000000,           3,     }},
                },
                Package()
                {
                    "FSTATE",
                    0x1, // F1 state
                    Package(){ "CLOCK", package(){ "fd_core_clk",                      2,          0,                1,     }},   					
                    Package(){ "CLOCK", package(){ "fd_core_uar_clk",                  2,          0,                0,     }},  
		            Package(){ "CLOCK", package(){ "fd_axi_clk",                       2,          0,                0,     }},                    
   		            Package(){ "CLOCK", package(){ "fd_ahb_clk",                       2,          0,                0,     }},
                },
           },
        },

    })

    Name(CPXC,
    Package ()
    { 
        //Device CAMS Data
        Package()
        {
            "DEVICE",
            "\\_SB.CAMS",
            Package()
            {
                    "DSTATE",
                    0x0, // D0 state
					
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_TOP",           1    }},
					
                    // Action:       1 == ENABLE 2 == DISABLE 3 == SET_FREQ 8 == EN_SETFREQ
                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST
                    //                                  Clock Name                 Action     Frequency       MatchType
                    //                                ---------                     ------     ----------     ----------
                    package(){ "CLOCK", package(){ "camss_csi0_clk",                 8,         266670000,      3,     }},
                    package(){ "CLOCK", package(){ "camss_phy0_csi0phytimer_clk",    8,         200000000,      3,     }}, 
                    package(){ "CLOCK", package(){ "camss_mclk0_clk",                8,         24000000,       3,     }},
                    //package(){ "CLOCK", package(){ "camss_gp0_clk",		     8,         24000000,       3,     }}, 
                    package(){ "CLOCK", package(){ "camss_csi_vfe0_clk",             1,         0,              1,     }},    
                    package(){ "CLOCK", package(){ "camss_csi_vfe1_clk",             1,         0,              1,     }},    
                    package(){ "CLOCK", package(){ "camss_csi0phy_clk",	             1,         0,              1,     }},
                    package(){ "CLOCK", package(){ "camss_csi0pix_clk",				 1,         0,              1,     }}, 
                    package(){ "CLOCK", package(){ "camss_csi0rdi_clk",				 1,         0,              1,     }}, 
                    package(){ "CLOCK", package(){ "camss_csi0_ahb_clk",			 1,         0,              1,     }},
                    package(){ "CLOCK", package(){ "camss_ispif_ahb_clk",			 1,		    0,              1,     }},
                },
                Package()
                {
                    "DSTATE",
                    0x3, // D3 state
                    package(){ "CLOCK", package(){ "camss_ispif_ahb_clk",	         2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi0_ahb_clk",			 2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi0rdi_clk",	             2,		    0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi0pix_clk",	             2,		    0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi0phy_clk",	             2,		    0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi_vfe0_clk",             2,		    0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi_vfe1_clk",             2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_mclk0_clk",		         2,		    0,              0,     }},
                    //package(){ "CLOCK", package(){ "camss_gp0_clk",	             2,	        0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_phy0_csi0phytimer_clk",    2,		    0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi0_clk",		         2,		    0,              0,     }},
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_TOP",           2}},
                },
            },
        //Device CAMF Data
        Package()
        {
            "DEVICE",
            "\\_SB.CAMF",
            Package()
           {
                   "DSTATE",
                    0x0, // D0 state
					
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_TOP",           1}},
					
                    // Action:       1 == ENABLE 2 == DISABLE 3 == SET_FREQ 8 == EN_SETFREQ
                    // MatchType:    1 == CLOCK_FREQUENCY_HZ_AT_LEAST 3 == CLOCK_FREQUENCY_HZ_CLOSEST
                                                  // Clock Name                 Action     Frequency            MatchType
                    //                                ---------                     ------     ----------     ----------
                    package(){ "CLOCK", package(){ "camss_csi0_clk",                 8,         266670000,      3,     }},
                    package(){ "CLOCK", package(){ "camss_csi2_clk",                 8,         266670000,      3,     }},
                    package(){ "CLOCK", package(){ "camss_phy2_csi2phytimer_clk",    8,         200000000,      3,     }},  
                    package(){ "CLOCK", package(){ "camss_mclk2_clk",                8,         24000000,       3,     }},
                  //package(){ "CLOCK", package(){ "gcc_gp1_clk",                    8,         24000000,       3,     }},
                    package(){ "CLOCK", package(){ "camss_csi_vfe0_clk",             1,         0,              1,     }},    
                    package(){ "CLOCK", package(){ "camss_csi_vfe1_clk",             1,         0,              1,     }},  
                    package(){ "CLOCK", package(){ "camss_csi2phy_clk",              1,         0,              1,     }},
                    package(){ "CLOCK", package(){ "camss_csi2pix_clk",              1,         0,              1,     }}, 
                    package(){ "CLOCK", package(){ "camss_csi2rdi_clk",              1,         0,              1,     }}, 
                    package(){ "CLOCK", package(){ "camss_csi2_ahb_clk",             1,         0,              1,     }},
                    package(){ "CLOCK", package(){ "camss_ispif_ahb_clk",            1,         0,              1,     }},
               },
               Package()
               {
                    "DSTATE",
                    0x3, // D3 state
                    package(){ "CLOCK", package(){ "camss_ispif_ahb_clk",            2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi2_ahb_clk",             2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi2rdi_clk",              2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi2pix_clk",              2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi2phy_clk",              2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi_vfe0_clk",             2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi_vfe1_clk",             2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_mclk2_clk",                2,         0,              0,     }},
                  //package(){ "CLOCK", package(){ "gcc_gp1_clk",                    2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_phy2_csi2phytimer_clk",    2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi2_clk",                 2,         0,              0,     }},
                    package(){ "CLOCK", package(){ "camss_csi0_clk",                 2,         0,              0,     }},     
                    Package(){ "FOOTSWITCH", Package(){ "VDD_CAMSS_TOP",           2}},
               },
            },
    })
}
