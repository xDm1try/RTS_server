from machine import I2C
from machine import ADC
from machine import Pin
from machine import Timer


VBUS_TYPE = ['NONE',
             'SDP',
             'CDP (1.5A)',
             'USB_DCP (3.25A)',
             'MAXC (1.5A)',
             'UNKNOWN (500mA)',
             'NONSTAND (1A/2A/2.1A/2.4A)',
             'VBUS_OTG']

CHRG_STAT = ['Not Charging',
             'Pre-charge',
             'Fast Charging',
             'Charge Termination Done']

PG_STAT = ['Not Power Good',
           'Power Good']

SDP_STAT = ['USB100 input is detected',
            'USB500 input is detected']

ADC_GAIN = [0, 1.334, 1.995, 3.548]
ADC_GAINstr = ['ATTN_0DB (0-1v)', 'ATTN_2_5DB(0-1.33v)', 'ATTN_6DB(0-2v)', 'ATTN_11DB(0-3.55v)']


class BQ25895v2:
    I2CADDR = const(0x6A)

    def __init__(self, i2c: I2C, intr_gpio: int, handler=None):
        self.i2c: I2C = i2c
        self._user_handler = handler
        self.reset()
        self.pq_stat_last = self.read_byte(0x0B) & 0b00000100
        self.pin_intr = Pin(intr_gpio, mode=Pin.IN, pull=Pin.PULL_UP)
        self.pin_intr.irq(trigger=Pin.IRQ_FALLING, handler=self._int_handler)  # FALLING ?

    def _int_handler(self, pin_o):
        print("BQ interrupted")
        REG0C1 = self.read_byte(0x0C)  # 1st read reports the pre-existing fault register
        REG0C2 = self.read_byte(0x0C)  # 2nd read reports the current fault register status
        REG0B = self.read_byte(0x0B)  # 2nd read reports the current fault register status
        print("0x0C1st:{:08b} 0x0C2nd:{:08b} 0x0B:{:08b}".format(REG0C1, REG0C2, REG0B))
        if self.pg_stat_last != REG0B & 0b00000100:
            self.pg_stat_last = REG0B & 0b00000100
            if REG0B & 0b00000100 > 1:
                print("RAZ pwr_uAH ")
        if self._user_handler is not None:
            self._user_handler(REG0C1, REG0C2, REG0B)

    def _setBit(self, reg: int, values: list[int | None]):
        if len(values) == 0:
            values.reverse()
            regVal = self.i2c.readfrom_mem(self.I2CADDR, reg, 1)[0]
            regValOld = regVal
            for i, value in enumerate(values):
                if value == 1:
                    mask = 1 << i
                    regVal = (regVal | mask)
                elif value == 0:
                    mask = !(1 << i)
                    regVal = (regVal & mask)
                if regValOld != regVal:
                    self.i2c.writeto_mem(self.I2CADDR, reg, regVal)
                    print("BQ>write : {} > {} to {:02X}".format(values, bin(regVal), reg))

    def read_byte(self, reg):
        regVal = self.i2c.readfrom_mem(self.I2CADDR, reg, 1)[0]
        return regVal

    def reset(self):
        self._setBit(0x14, [1, None, None, None, None, None, None, None])  # reset chip
        # ADC Conversion Rate Selection  – Start 1s Continuous Conversion
        self._setBit(0x02, [None, 1, None, None, None, None, None, None])
        self._setBit(0x07, [None, None, 0, 0, None, None, None, None])  # disable watchdog
        # self._setBit(0x00,[None,1,1,1,1,1,1,1])
        # self._setBit(0x04,[1,None,None,None,None,None,None,None])  #enable current pulse control
        # self._setBit(0x04,[None,None,None,None,None,None,1,None])   #enable current pulse control UP & DN

    def charge_enable(self, enable):
        self._setBit(0x03, [None, None, None, 1 if enable == True else 0, None, None, None])
        pass
    
    def vbus_type(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x0B, 1)
        return ret[0] >> 5

    def vbus_type_str(self):
        ret = self.vbus_type()
        return VBUS_TYPE[ret]

    def chrg_stat(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x0B, 1)
        return (ret[0] & 0b00011000) >> 3

    def chrg_stat_str(self):
        ret = self.chrg_stat()
        return CHRG_STAT[ret]
    
    def read_battery_percent(self):
        if self.chrg_stat():
            ret = 100
        else:
            vbat = self.read_battery_volt()
            if vbat >= 4200:
                ret = 100
            elif vbat <= 2800:
                ret = 0
            else:
                ret = int((vbat - 2800) / 1400 * 100)
        return ret


    def pg_stat(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x0B, 1)
        print("ret:{}".format(ret))
        return (ret[0] & 0b00000100) >> 2

    def pg_stat_str(self):
        ret = self.pg_stat()
        print("ret:{}".format(ret))
        return PG_STAT[ret]

    def vsys_stat(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x0B, 1)
        return (ret[0] & 0b00000001)

    def vsys_stat_str(self):
        ret = self.pg_stat()
        return "Regulation" if ret == 1 else "Not Regulation"
    

    def read_battery_volt(self):  # in mv
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x0E, 1)
        volt = 2304 + (int(ret[0] & 0b01111111) * 20)
        return volt

    def read_sys_volt(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x0F, 1)
        volt = 2304 + (int(ret[0] & 0b01111111) * 20)
        return volt

    def read_TS_per(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x10, 1)
        volt = 21 + (int(ret[0] & 0b01111111) * 0.465)
        return volt

    def read_stat(self):
        ret1 = self.i2c.readfrom_mem(self.I2CADDR, 0x0B, 1)
        ret2 = self.i2c.readfrom_mem(self.I2CADDR, 0x0C, 1)
        # print("0x0B:{:08b}, 0x0C:{:08b}".format(ord(ret1),ord(ret2)))
        return [ret1, ret2]

    def read_vbus_volt(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x11, 1)
        volt = 2600 + (int(ret[0] & 0b01111111) * 100)
        return volt

    def read_temperature(self):  # ???????????
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x10, 1)
        temp = 21 + (int(ret[0] & 0b01111111) * 0.465)
        return temp

    def read_charge_current(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x12, 1)
        amp = 0 + (int(ret[0] & 0b01111111) * 50)
        return amp


    def set_charge_current(self, m_A):
        if m_A > 5056:
            m_A = 5056
        regVal = int(m_A/64)
        self._setBit(0x04, [
            None,
            1 if (regVal & 0b01000000) > 0 else 0,
            1 if (regVal & 0b00100000) > 0 else 0,
            1 if (regVal & 0b00010000) > 0 else 0,
            1 if (regVal & 0b00001000) > 0 else 0,
            1 if (regVal & 0b00000100) > 0 else 0,
            1 if (regVal & 0b00000010) > 0 else 0,
            1 if (regVal & 0b00000001) > 0 else 0]
        )

    def read_input_current_max(self):
        ret = self.i2c.readfrom_mem(self.I2CADDR, 0x00, 1)
        amp = (100 + int(ret[0] & 0b00111111) * 50)
        return amp

    def set_input_current_max(self, m_A):
        if m_A > 3250:
            m_A = 3250
        elif m_A < 100:
            m_A = 100
        regVal = int((m_A - 100)/50)
        self._setBit(0x00, [
            None,
            None,
            1 if (regVal & 0b00100000) > 0 else 0,
            1 if (regVal & 0b00010000) > 0 else 0,
            1 if (regVal & 0b00001000) > 0 else 0,
            1 if (regVal & 0b00000100) > 0 else 0,
            1 if (regVal & 0b00000010) > 0 else 0,
            1 if (regVal & 0b00000001) > 0 else 0]
        )

    # inner class
    # Uniquement avec un ESP32 pour mesurer le courant d'entrée
    class POWER:
        # voltage taken from ILIM and amplified by an ampli op
        def __init__(self, bq25895):
            self._bq25895 = bq25895
            self.adc = ADC()
            self.p_SHDN_ = Pin('P21', mode=Pin.OUT)  # shutdown/enable ampli op
            self.pwr_ticks = utime.ticks_us()
            self.pwr_nAH = 0
            self.__alarm = Timer.Alarm(self.mesure, 1, periodic=True)

        def __del__(self):
            self.__alarm.cancel()
            self.__alarm = None

        def reset(self):
            print("BQ>reset chip")
            self.pwr_nAH = 0
            print("pwr_uAH", 0)

        def getPWR(self):  # en
            RILIM = 130
            KILIM = 365
            GAIN = 12.12
            self.p_SHDN_.value(1)
            utime.sleep_us(10)  # Enable Delay Time from Shutdown
            # ADC.ATTN_0DB (0-1), ADC.ATTN_2_5DB(0-1.33), ADC.ATTN_6DB(0-2), ADC.ATTN_11DB(0-3.55)
            ILIM = VILIM = 0
            ADC_GAIN = [0, 1.334, 1.995, 3.548]
            for i, e in reversed(list(enumerate(ADC_GAIN))):
                adc_ILIM = self.adc.channel(attn=i, pin='P20')
                ILIM = adc_ILIM()
                if ILIM < 2000 and i > 0:
                    pass
                else:
                    VILIM = adc_ILIM.voltage()
                    break
            if ILIM > 0:
                PWIN_I = (KILIM * (VILIM / GAIN)) / (RILIM * 0.8)
            elif self._bq25895.pg_stat() > 0:  # PYCOM mais prob avec ADC ESP32 pour faible valeur
                PWIN_I = 60.0
            else:
                PWIN_I = 0
            # print("ADC : {}, ADC_v = {}, PWIN_I : {}".format(adc_ILIM(), VILIM, PWIN_I) )
            self.p_SHDN_.value(0)
            l.debug("BQ>ATTN:{}, ILIM:{}, PWIN_I:{}".format(ADC_GAINstr[i], ILIM, PWIN_I))
            return PWIN_I

        def mesure(self, alarm):
            old = self.pwr_ticks
            self.pwr_ticks = utime.ticks_us()
            delta = utime.ticks_diff(self.pwr_ticks, old)
            self.pwr_nAH = self.pwr_nAH + int(self.getPWR() * delta / 3600)
            uAH = self.pwr_nAH // 1000
            # print("nAH : {}, uAH : {}".format(self.pwr_nAH, uAH))
            if uAH > 0:
                self.pwr_nAH = self.pwr_nAH - (uAH * 1000)
                uAH = pycom.nvs_get("pwr_uAH") + uAH
                # print("pwr_uAH :{}".format(uAH))
                pycom.nvs_set("pwr_uAH", uAH)

        @property
        def pwr_uAH(self):
            return pycom.nvs_get("pwr_uAH")

        @property
        def pwr_mAH(self):
            return int(round(pycom.nvs_get("pwr_uAH")/1000))