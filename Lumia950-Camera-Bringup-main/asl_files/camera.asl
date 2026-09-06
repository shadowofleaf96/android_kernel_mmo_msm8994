//
        //CAMERA PLATFORM
        //
        Device (CAMP)
        {
            Name (_DEP, Package(0x2)
            {
                \_SB_.PEP0,
                \_SB_.PMIC
            })

            Name (_HID, "QCOM245E")
            Name (_UID, 27)

            Method (_CRS, 0x0, NotSerialized)
            {
                Name (RBUF, ResourceTemplate ()
                {
                    //MMSS_A_CCI
                    Memory32Fixed (ReadWrite, 0xFDA0C000, 0x0003fff)

                    //MMSS_A_CAMSS
                    Memory32Fixed (ReadWrite, 0xFDA00000, 0x00000047)

                    //MMSS_A_CCI
                    Interrupt(ResourceConsumer, Edge, ActiveHigh, Exclusive, , , ) {82}

                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){92} //CAMSENSOR_1_RST_N
                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){91} //CAMSENSOR_1_STANBY
                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){102} //CAMSENSOR_2_RST_N
                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){106} //CAMSENSOR_2_STANBY
                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){104} //WEBCAM1_RST_N
                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){105} //WEBCAM1_STANBY_N        

                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){12}        
                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){8}     
                    GpioIo(Exclusive,PullNone,0,0, ,"\\_SB.GIO0", ,){21}     
                    GpioIo(Exclusive,PullDown,0,0, ,"\\_SB.PM02", ,){0x508}          
                })
                Return (RBUF)
     
            }

            Method (INFO)
            {
                // INFO is 32 bit number that determines the sensor orientation and I2C bus used by camera
                // bits 0-1 back sensor orientation, bit 0 : mirrorred if 1, bit 1 : flipped if 1
                // bits 8-15 front sensor orientation, bit 8 : mirrorred if 1, bit 9 : flipped if 1              
                // bits 10-15 not used
                // bit 16 front sensor I2C bus. I2C bus 0 if 0 else I2C bus 1
                // bit 17 back sensor I2C bus.  I2C bus 0 if 0 else I2C bus 1
                // bits 18-19 are unused
                // bit 20 represents PMIC flash LED configuration. 0 = PMIC_FLASH_LED_CONFIG_0, 1 = PMIC_FLASH_LED_CONFIG_1
                // bit  24-27 represent CSID. 00 = CSDI0, 01 = CSID1, 10 = CSID2, 11 = CSID3
                // bits 28-31 are unused
                // 31   | 27   | 23   | 19      | 15   | 11      | 7    | 3 
                //      |   cc |      |     i i |      |     f m |      |     f m
                // 0000 | 0000 | 0000 | 0 0 0 0 | 0000 | 0 0 0 0 | 0000 | 0 0 0 0
                Return(0x060000)

            }      
        }

        //
        // CAMERA SENSOR
        //
        Device (CAMS)
        {
            Name (_DEP, Package(0x2)
            {
                \_SB_.CAMP,
                \_SB_.PEP0
            })

            Name (_HID, "QCOM2434")
            Name (_UID, 21)

            Method (_CRS, 0x0, NotSerialized)
            {
                Name (RBUF, ResourceTemplate ()
                {
                    // MMSS_A_CSID_0
                    Memory32Fixed (ReadWrite, 0xFDA08000, 0x000003FF)
                    // MMSS_A_CSI_PHY_0
                    Memory32Fixed (ReadWrite, 0xFDA0AC00, 0x000003FF)

                    // MMSS_A_CSID_0 Interrupt
                    Interrupt(ResourceConsumer, Edge, ActiveHigh, Exclusive, , , ) {83}
                })
                Return (RBUF)
            }		
            // PEP Proxy Support
            Name(PGID, Buffer(10) {"\\_SB.CAMS"})   // Device ID buffer - PGID( Pep given ID )

            Name(DBUF, Buffer(DBFL) {})           // Device ID buffer - PGID( Pep given ID )
            CreateByteField(DBUF, 0x0, STAT)    // STATUS 1 BYTE
                                                // HIDDEN 1 BYTE ( SIZE )
            CreateByteField(DBUF, 2, DVAL )     // Packet value, 1 BYTES Device Status
            CreateField(DBUF, 24, 160, DEID)    // Device ID, 20 BYTES(160 Bits)
 
            Method (_S1D, 0) { Return (3) }     // S1 => D3
            Method (_S2D, 0) { Return (3) }     // S2 => D3
            Method (_S3D, 0) { Return (3) }     // S3 => D3
            
            Method(_PS0, 0x0, NotSerialized) 
            {
                Store(Buffer(ESNL){}, DEID) 
                Store(0, DVAL)
                Store(PGID, DEID)
                If(\_SB.ABD.AVBL)
                {
                Store(DBUF, \_SB.PEP0.FLD0)
            }
            }
            Method(_PS3, 0x0, NotSerialized) 
            {
                Store(Buffer(ESNL){}, DEID) 
                Store(3, DVAL)
                Store(PGID, DEID)
                If(\_SB.ABD.AVBL)
                {
                Store(DBUF, \_SB.PEP0.FLD0)
            }
            }
        }
        Device (CAMF)
        {
            Name (_DEP, Package(0x3)
            {
                \_SB_.CAMP,
                \_SB_.PEP0,
                \_SB_.CAMS
            })

            Name (_HID, "QCOM2439")
            Name (_UID, 26)

            Method (_CRS, 0x0, NotSerialized)
            {
                Name (RBUF, ResourceTemplate ()
                {
                    // MMSS_A_CSID_2
                    Memory32Fixed (ReadWrite, 0xFDA08800, 0x000003FF)
                    // MMSS_A_CSI_PHY_2
                    Memory32Fixed (ReadWrite, 0xFDA0B400, 0x000003FF)

                    // MMSS_A_CSID_2 Interrupt
                    Interrupt(ResourceConsumer, Edge, ActiveHigh, Exclusive, , , ) {85}
                })
                Return (RBUF)
            }		
            // PEP Proxy Support
            Name(PGID, Buffer(10) {"\\_SB.CAMF"})   // Device ID buffer - PGID( Pep given ID )

            Name(DBUF, Buffer(DBFL) {})           // Device ID buffer - PGID( Pep given ID )
            CreateByteField(DBUF, 0x0, STAT)    // STATUS 1 BYTE
                                                // HIDDEN 1 BYTE ( SIZE )
            CreateByteField(DBUF, 2, DVAL )     // Packet value, 1 BYTES Device Status
            CreateField(DBUF, 24, 160, DEID)    // Device ID, 20 BYTES(160 Bits)
 
            Method (_S1D, 0) { Return (3) }     // S1 => D3
            Method (_S2D, 0) { Return (3) }     // S2 => D3
            Method (_S3D, 0) { Return (3) }     // S3 => D3
            
            Method(_PS0, 0x0, NotSerialized) 
            {
                Store(Buffer(ESNL){}, DEID) 
                Store(0, DVAL)
                Store(PGID, DEID)
                If(\_SB.ABD.AVBL)
                {
                Store(DBUF, \_SB.PEP0.FLD0)
            }
            }
            Method(_PS3, 0x0, NotSerialized) 
            {
                Store(Buffer(ESNL){}, DEID) 
                Store(3, DVAL)
                Store(PGID, DEID)
                If(\_SB.ABD.AVBL)
                {
                Store(DBUF, \_SB.PEP0.FLD0)
            }
            }
        }
        Device (CAMT)
        {
            Name (_DEP, Package(0x3)
            {
                \_SB_.CAMP,
                \_SB_.PEP0,
                \_SB_.CAMF
            })

            Name (_HID, "QCOM2436")
            Name (_UID, 28)

            Method (_CRS, 0x0, NotSerialized)
            {
                Name (RBUF, ResourceTemplate ()
                {
                    Memory32Fixed (ReadWrite, 0xFDA08C00, 0x000003FF)
                    Interrupt(ResourceConsumer, Edge, ActiveHigh, Exclusive, , , ) {86}
                })
                Return (RBUF)
            }		
            // PEP Proxy Support
            Name(PGID, Buffer(10) {"\\_SB.CAMT"})   // Device ID buffer - PGID( Pep given ID )

            Name(DBUF, Buffer(DBFL) {})           // Device ID buffer - PGID( Pep given ID )
            CreateByteField(DBUF, 0x0, STAT)    // STATUS 1 BYTE
                                                // HIDDEN 1 BYTE ( SIZE )
            CreateByteField(DBUF, 2, DVAL )     // Packet value, 1 BYTES Device Status
            CreateField(DBUF, 24, 160, DEID)    // Device ID, 20 BYTES(160 Bits)
 
            Method (_S1D, 0) { Return (3) }     // S1 => D3
            Method (_S2D, 0) { Return (3) }     // S2 => D3
            Method (_S3D, 0) { Return (3) }     // S3 => D3
            
            Method(_PS0, 0x0, NotSerialized) 
            {
                Store(Buffer(ESNL){}, DEID) 
                Store(0, DVAL)
                Store(PGID, DEID)
                If(\_SB.ABD.AVBL)
                {
                Store(DBUF, \_SB.PEP0.FLD0)
            }
            }
            Method(_PS3, 0x0, NotSerialized) 
            {
                Store(Buffer(ESNL){}, DEID) 
                Store(3, DVAL)
                Store(PGID, DEID)
                If(\_SB.ABD.AVBL)
                {
                Store(DBUF, \_SB.PEP0.FLD0)
            }
            }
        }

    //
    // CAMERA WHITE LED FLASH
    //
    Device (FLSH)
        {
            Name (_DEP, Package(0x3)
            {
                \_SB_.CAMF,
                \_SB_.CAMS,
                \_SB_.PEP0
            })
            
            Name (_HID, "QCOM244B")
            Name (_UID, 25)
            
            Method (_CRS, 0x0, NotSerialized)
             {
                Name (RBUF, ResourceTemplate ()
                {
                    //  GpioInt (EdgeLevel, ActiveLevel, Shared, PinConfig, DebounceTimeout, ResourceSource,
                    //           ResourceSourceIndex, ResourceUsage, DescriptorName, VendorData) {PinList}

                    // LED fault (short/open/thrm drt/vreg_ok)
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9D} 

                    // LED1_RMP_UP_DONE_RT_STS
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9B}

                    // LED2_RMP_UP_DONE_RT_STS
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE99}

                    // Low Vph_pwr detect (Vph_pwr < threshold)
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9C}

                    // Flash Safety timer expiration
                    //GpioInt(Edge, ActiveBoth, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9F} 
                })
                Return (RBUF)
            }
        }

    //
    // CAMERA WHITE LED FLASH
    //
    Device (FLHT)
        {
            Name (_DEP, Package(0x3)
            {
                \_SB_.CAMT,
                \_SB_.PEP0,
                \_SB_.FLSH
            })
            
            Name (_HID, "QCOM244C")
            Name (_UID, 29)
            
            Method (_CRS, 0x0, NotSerialized)
             {
                Name (RBUF, ResourceTemplate ()
                {
                    //  GpioInt (EdgeLevel, ActiveLevel, Shared, PinConfig, DebounceTimeout, ResourceSource,
                    //           ResourceSourceIndex, ResourceUsage, DescriptorName, VendorData) {PinList}

                    // LED fault (short/open/thrm drt/vreg_ok)
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9D} 

                    // LED1_RMP_UP_DONE_RT_STS
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9B}

                    // LED2_RMP_UP_DONE_RT_STS
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE99}

                    // Low Vph_pwr detect (Vph_pwr < threshold)
                    //GpioInt(Edge, ActiveHigh, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9C}

                    // Flash Safety timer expiration
                    //GpioInt(Edge, ActiveBoth, Exclusive, PullUp, 6200, "\\_SB.PM01", , ) {0xE9F} 

                    GpioInt(Level, ActiveHigh, Shared, PullDown, 0, "\\_SB.PM02", , ) {0xE9F} 
                    GpioInt(Level, ActiveHigh, Shared, PullDown, 0, "\\_SB.PM02", , ) {0xE9E} 
                    GpioIo(Shared,PullDown,0,0, ,"\\_SB.PM02", ,){0xE9F}    
                    GpioIo(Shared,PullDown,0,0, ,"\\_SB.PM02", ,){0xE9E}    
                })
                Return (RBUF)
            }
        }

        //
        // Hardware JPEG Encoder
        //
        Device (JPGE)
        {
            Name (_DEP, Package(0x3)
            {
                \_SB_.CAMP,
                \_SB_.MMU2,
                \_SB_.PEP0
            })

            Name (_HID, "QCOM2467")
            Name (_UID, 23)

            Method (_CRS, 0x0, NotSerialized) {
                Name (RBUF, ResourceTemplate ()
                {
                    // HW JPEG Encoder 0 register space
                    Memory32Fixed (ReadWrite, 0xFDA1C000, 0x00000320)
                    
                    // VBIF address space shared by the HW JPEG Encoder 1 & 2, and the HW JPEG Decoder
                    // 0xFDA60C30 - 0xFDA60000 + 4
                    Memory32Fixed (ReadWrite, 0xFDA60000, 0x00000C34)
                    
                    // JPEGE 0 Interrupt
                    Interrupt(ResourceConsumer, Edge, ActiveHigh, Exclusive, , , ) {91}

                    // HW JPEG Encoder 1 register space
                    Memory32Fixed (ReadWrite, 0xFDA20000, 0x00000320)
                    
                    // JPEGE 1 Interrupt
                    Interrupt(ResourceConsumer, Edge, ActiveHigh, Exclusive, , , ) {92}

                    // HW DMA register space
                    Memory32Fixed (ReadWrite, 0xFDAA0000, 0x000001A0)

                    // JEPG 3 (DMA) Interrupt
                    Interrupt(ResourceConsumer, Edge, ActiveHigh, Exclusive, , , ) {336}
                })
                Return (RBUF)
            }
        }
