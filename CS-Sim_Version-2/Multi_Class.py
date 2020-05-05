class Msg_Header:
    class Msg_ID:
        MU_ID = '0'
        MUA_ID = '1'
        MUB_ID = '2'
        VOIP_ID = '63'
        IFUC1_ID = '64'
        IFUC2_ID = '65'
        PTP1_ID = '61'
        PTP2_ID = '62'
        SW1_ID = '66'
        SW2_ID = '67'
        GW1_ID = '68'
        GW2_ID= '69'

    class Msg_Code:
        VOIP_STS = '0210'
        VCSS_SW = '0220'
        IPL_SW = '0230'
        TID1_SW = '0240'
        TID2_SW = '0250'
        TID3_SW = '0260'

        IFUC_STS = '0121'
        IFUC_SLT_STS = '0221'
        IFUC_LNK_STS = '0321'
        IFUC_SW = '0421'

        PTP_STSr = '2210'
        PTP_SW = '2220'

        SW_STS = '3210'
        SW_FO_STS = '3220'
        SW_SW = '3230'

        GW_SW = '4220'



