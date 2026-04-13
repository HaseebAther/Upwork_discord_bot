import requests

cookies = {
    'visitor_id': '182.180.17.171.1776074003777000',
    'enabled_ff': '!CI12577UniversalSearch,!CmpLibOn,!Fluid,!MP16400Air3Migration,!SSINavUser,!i18nGA,CI17409DarkModeUI,JPAir3,OTBnrOn,SSINavUserBpa,TONB2256Air3Migration,i18nOn',
    'country_code': 'PK',
    'cookie_prefix': '',
    'cookie_domain': '.upwork.com',
    '__cflb': '02DiuEXPXZVk436fJfSVuuwDqLqkhavJakM1xB4YYT9T1',
    'x-spec-id': 'bdcb9fa7-fdc0-4635-a932-3135304e890c',
    'umq': '1366',
    '_cfuvid': '5bQewBKD6kR_Ii5r7VCnDMUeR32Dd7c8Hs47NxlyEnk-1776074008.4001355-1.0.1.1-mYWNiTLv2ufgoI6aS4DPxDpnYTjCWGJhL1hoJfYg75Y',
    '_upw_ses.5831': '*',
    'spt': '46008e1e-cd8e-49c2-b71d-c969eeb1f2c7',
    '_gcl_au': '1.1.80314547.1776074012',
    '_cq_duid': '1.1776074012.4UjMQpj1vpUqsWVL',
    '_cq_suid': '1.1776074012.D1aviyB9DVNPbEnN',
    'OptanonAlertBoxClosed': '2026-04-13T09:53:34.346Z',
    '_ga': 'GA1.1.2047709191.1776074019',
    '__pdst': '0b747d5ea2734ed88cee7e598c5ae707',
    '_twpid': 'tw.1776074019803.295665589824348959',
    '__ps_r': '_',
    '__ps_lu': 'https://www.upwork.com/nx/search/jobs/?q=youtube+video+seo&__cf_chl_tk=OGxnPuIaDYqMiwywi7ZIuXbntklTG4k3ksUOGsIz43Q-1776073998-1.0.1.1-WR5kIg7Z9lV12BEgF42Jra_lAiwLzOaZLYwuzYXZCyo',
    '__ps_did': 'pscrb_de048352-fa85-468e-9784-afe365a0d693',
    '__ps_fva': '1776074019985',
    '_fbp': 'fb.1.1776074021083.84074212169566861',
    '_tt_enable_cookie': '1',
    '_ttp': '01KP345PEG33PS77HK2M6HNDT6_.tt.1',
    'IR_gbd': 'upwork.com',
    '__ps_sr': '_',
    '__ps_slu': 'https://www.upwork.com/nx/search/jobs/?q=youtube+video&__cf_chl_tk=8tj1SGtJQkPYa3RCysX8sFhmk4Ny2C0bjSTeQrmUNSw-1776076166-1.0.1.1-6T7l0fPonOpU3drqzRpuRCMr64apfzjIYXXrsHEq1q4',
    'cf_clearance': 'aVHEL5irri8Np7Nh5Enatup_r9RAue0HOE905vlYPV4-1776078641-1.2.1.1-Wij.DK2M7h2FDbnUO1TOvvlLwV7l7bxR9FgVjMdSQj0zhKFfx3Jm77DNJVv.tCYYTNYNRb44.qWWF0EKkEOpS7w0qEQidjSubNJPCkZ5_36Z3mZgi7Ao9mocZJkPeoNzi1I4UzajaB8b1RC5bH0JpV3vwuI2cNmxPF8L_7d84GmuFYpoXsaXQrG40pKsXlphdlmwF_VQI1zAQChVpabxbEP_fHqVMQ_kDtwfFSep6mU6UvDbrLDRzA90GPVLaSSmKejXtw__ngj2kcwCu3sc.qWkqfr8Orz567I1AqgWZ4V2SbiyrRfK1gmW_51acocDgjmhT5sUWr759IPN4Ca2LQ',
    '__cf_bm': 'h.urXORaVJ6VAn2BByPXgCnCCe3P0RLTffS7IE9v_6k-1776078641.227669-1.0.1.1-YzOy.JN2I77_DD6eHZEKws4fRjPY243uklIryLlU13yCTtWJX1DMP6g5c8jikk0cslEBF5BYTPEcSP6mx1IpPYc1x_4EnMxnrxhuaJpkG5n3R6lSEpjwSMBOG3o5tPky',
    'visitor_gql_token': 'oauth2v2_int_ed622b1688b05737fc7983336e375bf2',
    '_vwo_uuid_v2': 'D5C204303ED747D18E88254367A93AFF2|ec5b394f32c4560e73285f2541e4b921',
    'XSRF-TOKEN': 'rOn25VxrDnSrvqTv4nvQEvlLqON2x9zD',
    '_vwo_uuid': 'D5C204303ED747D18E88254367A93AFF2',
    '_vwo_ds': '3%241776078714%3A31.08142762%3A%3A%3A%3A%3A1776078714%3A1776078714%3A1',
    '_vis_opt_s': '1%7C',
    '_vis_opt_test_cookie': '1',
    'g_state': '{"i_l":0,"i_ll":1776078723828,"i_b":"4GXich47wrX6IYtkQDTr6LWXpCdIzGPkzBT2f3/Ta5I","i_e":{"enable_itp_optimization":18},"i_et":1776078723828}',
    'up_g_one_tap_closed': 'true',
    'SeoPagesNuxt_vt': 'oauth2v2_int_46073a9a853e76bb64fbb1267d561de2',
    '_vwo_sn': '0%3A2%3A%3A%3A%3A%3A21',
    'UniversalSearchNuxt_vt': 'oauth2v2_int_0f6c0928243b3ea84b94b6a02e841744',
    'AWSALBTG': 'UKLio+ieqXn1cNQXeFHtfJUuHxoH+I9DRor4reH5EDW52GXli8DbfkWwkTUqAugMhxK4NKtXWcLX/dwj2ahy/aQ9RatFX0vf6ow+/CQRgei8stDZZ1S0Z8+xIhrMF8Tf51WWAiXrYDkcdYiECcVq0YXajGdUIwnotGLeEAgoETPC',
    'AWSALBTGCORS': 'UKLio+ieqXn1cNQXeFHtfJUuHxoH+I9DRor4reH5EDW52GXli8DbfkWwkTUqAugMhxK4NKtXWcLX/dwj2ahy/aQ9RatFX0vf6ow+/CQRgei8stDZZ1S0Z8+xIhrMF8Tf51WWAiXrYDkcdYiECcVq0YXajGdUIwnotGLeEAgoETPC',
    'OptanonConsent': 'consentId=8244a87d-5e50-4da4-9a70-fd944bcbb7b0&datestamp=Mon+Apr+13+2026+16%3A12%3A29+GMT%2B0500+(Pakistan+Standard+Time)&version=202512.1.0&isAnonUser=1&isGpcEnabled=0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&interactionCount=1&landingPath=NotLandingPage&iType=3&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&crTime=1776074015270&intType=3&geolocation=PK%3BPB&AwaitingReconsent=false',
    '_rdt_uuid': '1776074019779.d40344f2-860c-4a48-b3f8-fba433a7aacb',
    '_ga_KSM221PNDX': 'GS2.1.s1776076186$o2$g1$t1776078752$j21$l0$h0',
    'forterToken': '8e46fb9ce6424b2fb192aebb7d2ec570_1776078748073__UDF43-m4_23ck_6T8s++UsWek%3D-10599-v2',
    'forterToken': '8e46fb9ce6424b2fb192aebb7d2ec570_1776078748073__UDF43-m4_23ck_6T8s++UsWek%3D-10599-v2',
    'IR_13634': '1776078752943%7C0%7C1776078752943%7C%7C',
    '_uetsid': 'a6c87d50371e11f1b678514cb7f1e7b8',
    '_uetvid': 'a6c8c870371e11f1b1aed119d3bcbde9',
    'ttcsid_CGCUGEBC77UAPU79F02G': '1776074021348::EkaKS3Xum4Ph-r2DLXfQ.1.1776078755247.1',
    '_cq_session': '1.1776074012780.ks1V15fNqvLvxAgy.1776078790845',
    'AWSALB': '9gws+7KFWxnBKXxrKHrlFZMeFccNrG06kfbQUpi3KhOsdjhdeSyuLYNCojRPyf25UG7Zft8g3fqSHFNPpUCgphJs9qrj4gRsuq/XBYPW06T9euShcCRVPNOSyP+b',
    'AWSALBCORS': '9gws+7KFWxnBKXxrKHrlFZMeFccNrG06kfbQUpi3KhOsdjhdeSyuLYNCojRPyf25UG7Zft8g3fqSHFNPpUCgphJs9qrj4gRsuq/XBYPW06T9euShcCRVPNOSyP+b',
    'usnGlobalParams': '%7B%22isAutosuggest%22%3A1%2C%22autosuggestion%22%3A%7B%22label%22%3A%22youtube%20video%20editor%22%2C%22iconImport%22%3A%7B%22staticRenderFns%22%3A%5B%5D%2C%22_compiled%22%3Atrue%2C%22_Ctor%22%3A%7B%7D%7D%2C%22type%22%3A%22suggestion%22%2C%22id%22%3A%22youtube-0%22%7D%7D',
    '_upw_id.5831': '279b5cb6-d63c-4c89-aa11-07fc9e17cdfb.1776074012.1.1776078792..af6b4849-d78a-4401-895c-54b2a33f5b69..24592593-07e0-4968-81ba-082cf2431e92.1776074011925.183',
    'ttcsid': '1776074021350::47bZfJkBL_5Il6hCcq1P.1.1776078755247.0::1.4771204.4732243::4769391.41.381.168::4768674.18.0',
}

headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'authorization': 'Bearer oauth2v2_int_0f6c0928243b3ea84b94b6a02e841744',
    'content-type': 'application/json',
    'origin': 'https://www.upwork.com',
    'priority': 'u=1, i',
    'referer': 'https://www.upwork.com/nx/search/jobs/?q=youtube%20video%20editor',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"146.0.7680.178"',
    'sec-ch-ua-full-version-list': '"Chromium";v="146.0.7680.178", "Not-A.Brand";v="24.0.0.0", "Google Chrome";v="146.0.7680.178"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"10.0.0"',
    'sec-ch-viewport-width': '1366',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'vnd-eo-parent-span-id': '37e562b4-b408-4a1e-bfee-a6eed8a01e42',
    'vnd-eo-span-id': '4668824e-e44d-441a-b537-7683b3bb5927',
    'vnd-eo-trace-id': '9eba0919670a03e8-KHI',
    'vnd-eo-visitorid': '182.180.17.171.1776074003777000',
    'x-upwork-accept-language': 'en-US',
    # 'cookie': 'visitor_id=182.180.17.171.1776074003777000; enabled_ff=!CI12577UniversalSearch,!CmpLibOn,!Fluid,!MP16400Air3Migration,!SSINavUser,!i18nGA,CI17409DarkModeUI,JPAir3,OTBnrOn,SSINavUserBpa,TONB2256Air3Migration,i18nOn; country_code=PK; cookie_prefix=; cookie_domain=.upwork.com; __cflb=02DiuEXPXZVk436fJfSVuuwDqLqkhavJakM1xB4YYT9T1; x-spec-id=bdcb9fa7-fdc0-4635-a932-3135304e890c; umq=1366; _cfuvid=5bQewBKD6kR_Ii5r7VCnDMUeR32Dd7c8Hs47NxlyEnk-1776074008.4001355-1.0.1.1-mYWNiTLv2ufgoI6aS4DPxDpnYTjCWGJhL1hoJfYg75Y; _upw_ses.5831=*; spt=46008e1e-cd8e-49c2-b71d-c969eeb1f2c7; _gcl_au=1.1.80314547.1776074012; _cq_duid=1.1776074012.4UjMQpj1vpUqsWVL; _cq_suid=1.1776074012.D1aviyB9DVNPbEnN; OptanonAlertBoxClosed=2026-04-13T09:53:34.346Z; _ga=GA1.1.2047709191.1776074019; __pdst=0b747d5ea2734ed88cee7e598c5ae707; _twpid=tw.1776074019803.295665589824348959; __ps_r=_; __ps_lu=https://www.upwork.com/nx/search/jobs/?q=youtube+video+seo&__cf_chl_tk=OGxnPuIaDYqMiwywi7ZIuXbntklTG4k3ksUOGsIz43Q-1776073998-1.0.1.1-WR5kIg7Z9lV12BEgF42Jra_lAiwLzOaZLYwuzYXZCyo; __ps_did=pscrb_de048352-fa85-468e-9784-afe365a0d693; __ps_fva=1776074019985; _fbp=fb.1.1776074021083.84074212169566861; _tt_enable_cookie=1; _ttp=01KP345PEG33PS77HK2M6HNDT6_.tt.1; IR_gbd=upwork.com; __ps_sr=_; __ps_slu=https://www.upwork.com/nx/search/jobs/?q=youtube+video&__cf_chl_tk=8tj1SGtJQkPYa3RCysX8sFhmk4Ny2C0bjSTeQrmUNSw-1776076166-1.0.1.1-6T7l0fPonOpU3drqzRpuRCMr64apfzjIYXXrsHEq1q4; cf_clearance=aVHEL5irri8Np7Nh5Enatup_r9RAue0HOE905vlYPV4-1776078641-1.2.1.1-Wij.DK2M7h2FDbnUO1TOvvlLwV7l7bxR9FgVjMdSQj0zhKFfx3Jm77DNJVv.tCYYTNYNRb44.qWWF0EKkEOpS7w0qEQidjSubNJPCkZ5_36Z3mZgi7Ao9mocZJkPeoNzi1I4UzajaB8b1RC5bH0JpV3vwuI2cNmxPF8L_7d84GmuFYpoXsaXQrG40pKsXlphdlmwF_VQI1zAQChVpabxbEP_fHqVMQ_kDtwfFSep6mU6UvDbrLDRzA90GPVLaSSmKejXtw__ngj2kcwCu3sc.qWkqfr8Orz567I1AqgWZ4V2SbiyrRfK1gmW_51acocDgjmhT5sUWr759IPN4Ca2LQ; __cf_bm=h.urXORaVJ6VAn2BByPXgCnCCe3P0RLTffS7IE9v_6k-1776078641.227669-1.0.1.1-YzOy.JN2I77_DD6eHZEKws4fRjPY243uklIryLlU13yCTtWJX1DMP6g5c8jikk0cslEBF5BYTPEcSP6mx1IpPYc1x_4EnMxnrxhuaJpkG5n3R6lSEpjwSMBOG3o5tPky; visitor_gql_token=oauth2v2_int_ed622b1688b05737fc7983336e375bf2; _vwo_uuid_v2=D5C204303ED747D18E88254367A93AFF2|ec5b394f32c4560e73285f2541e4b921; XSRF-TOKEN=rOn25VxrDnSrvqTv4nvQEvlLqON2x9zD; _vwo_uuid=D5C204303ED747D18E88254367A93AFF2; _vwo_ds=3%241776078714%3A31.08142762%3A%3A%3A%3A%3A1776078714%3A1776078714%3A1; _vis_opt_s=1%7C; _vis_opt_test_cookie=1; g_state={"i_l":0,"i_ll":1776078723828,"i_b":"4GXich47wrX6IYtkQDTr6LWXpCdIzGPkzBT2f3/Ta5I","i_e":{"enable_itp_optimization":18},"i_et":1776078723828}; up_g_one_tap_closed=true; SeoPagesNuxt_vt=oauth2v2_int_46073a9a853e76bb64fbb1267d561de2; _vwo_sn=0%3A2%3A%3A%3A%3A%3A21; UniversalSearchNuxt_vt=oauth2v2_int_0f6c0928243b3ea84b94b6a02e841744; AWSALBTG=UKLio+ieqXn1cNQXeFHtfJUuHxoH+I9DRor4reH5EDW52GXli8DbfkWwkTUqAugMhxK4NKtXWcLX/dwj2ahy/aQ9RatFX0vf6ow+/CQRgei8stDZZ1S0Z8+xIhrMF8Tf51WWAiXrYDkcdYiECcVq0YXajGdUIwnotGLeEAgoETPC; AWSALBTGCORS=UKLio+ieqXn1cNQXeFHtfJUuHxoH+I9DRor4reH5EDW52GXli8DbfkWwkTUqAugMhxK4NKtXWcLX/dwj2ahy/aQ9RatFX0vf6ow+/CQRgei8stDZZ1S0Z8+xIhrMF8Tf51WWAiXrYDkcdYiECcVq0YXajGdUIwnotGLeEAgoETPC; OptanonConsent=consentId=8244a87d-5e50-4da4-9a70-fd944bcbb7b0&datestamp=Mon+Apr+13+2026+16%3A12%3A29+GMT%2B0500+(Pakistan+Standard+Time)&version=202512.1.0&isAnonUser=1&isGpcEnabled=0&browserGpcFlag=0&isIABGlobal=false&identifierType=Cookie+Unique+Id&hosts=&interactionCount=1&landingPath=NotLandingPage&iType=3&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&crTime=1776074015270&intType=3&geolocation=PK%3BPB&AwaitingReconsent=false; _rdt_uuid=1776074019779.d40344f2-860c-4a48-b3f8-fba433a7aacb; _ga_KSM221PNDX=GS2.1.s1776076186$o2$g1$t1776078752$j21$l0$h0; forterToken=8e46fb9ce6424b2fb192aebb7d2ec570_1776078748073__UDF43-m4_23ck_6T8s++UsWek%3D-10599-v2; forterToken=8e46fb9ce6424b2fb192aebb7d2ec570_1776078748073__UDF43-m4_23ck_6T8s++UsWek%3D-10599-v2; IR_13634=1776078752943%7C0%7C1776078752943%7C%7C; _uetsid=a6c87d50371e11f1b678514cb7f1e7b8; _uetvid=a6c8c870371e11f1b1aed119d3bcbde9; ttcsid_CGCUGEBC77UAPU79F02G=1776074021348::EkaKS3Xum4Ph-r2DLXfQ.1.1776078755247.1; _cq_session=1.1776074012780.ks1V15fNqvLvxAgy.1776078790845; AWSALB=9gws+7KFWxnBKXxrKHrlFZMeFccNrG06kfbQUpi3KhOsdjhdeSyuLYNCojRPyf25UG7Zft8g3fqSHFNPpUCgphJs9qrj4gRsuq/XBYPW06T9euShcCRVPNOSyP+b; AWSALBCORS=9gws+7KFWxnBKXxrKHrlFZMeFccNrG06kfbQUpi3KhOsdjhdeSyuLYNCojRPyf25UG7Zft8g3fqSHFNPpUCgphJs9qrj4gRsuq/XBYPW06T9euShcCRVPNOSyP+b; usnGlobalParams=%7B%22isAutosuggest%22%3A1%2C%22autosuggestion%22%3A%7B%22label%22%3A%22youtube%20video%20editor%22%2C%22iconImport%22%3A%7B%22staticRenderFns%22%3A%5B%5D%2C%22_compiled%22%3Atrue%2C%22_Ctor%22%3A%7B%7D%7D%2C%22type%22%3A%22suggestion%22%2C%22id%22%3A%22youtube-0%22%7D%7D; _upw_id.5831=279b5cb6-d63c-4c89-aa11-07fc9e17cdfb.1776074012.1.1776078792..af6b4849-d78a-4401-895c-54b2a33f5b69..24592593-07e0-4968-81ba-082cf2431e92.1776074011925.183; ttcsid=1776074021350::47bZfJkBL_5Il6hCcq1P.1.1776078755247.0::1.4771204.4732243::4769391.41.381.168::4768674.18.0',
}

params = {
    'alias': 'visitorJobSearch',
}

json_data = {
    'query': '\n  query VisitorJobSearch($requestVariables: VisitorJobSearchV1Request!) {\n    search {\n      universalSearchNuxt {\n        visitorJobSearchV1(request: $requestVariables) {\n          paging {\n            total\n            offset\n            count\n          }\n          \n    facets {\n      jobType \n    {\n      key\n      value\n    }\n  \n      workload \n    {\n      key\n      value\n    }\n  \n      clientHires \n    {\n      key\n      value\n    }\n  \n      durationV3 \n    {\n      key\n      value\n    }\n  \n      amount \n    {\n      key\n      value\n    }\n  \n      contractorTier \n    {\n      key\n      value\n    }\n  \n      contractToHire \n    {\n      key\n      value\n    }\n  \n      \n    }\n  \n          results {\n            id\n            title\n            description\n            relevanceEncoded\n            ontologySkills {\n              uid\n              parentSkillUid\n              prefLabel\n              prettyName: prefLabel\n              freeText\n              highlighted\n            }\n            \n            jobTile {\n              job {\n                id\n                ciphertext: cipherText\n                jobType\n                weeklyRetainerBudget\n                hourlyBudgetMax\n                hourlyBudgetMin\n                hourlyEngagementType\n                contractorTier\n                sourcingTimestamp\n                createTime\n                publishTime\n                \n                hourlyEngagementDuration {\n                  rid\n                  label\n                  weeks\n                  mtime\n                  ctime\n                }\n                fixedPriceAmount {\n                  isoCurrencyCode\n                  amount\n                }\n                fixedPriceEngagementDuration {\n                  id\n                  rid\n                  label\n                  weeks\n                  ctime\n                  mtime\n                }\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n  ',
    'variables': {
        'requestVariables': {
            'userQuery': 'youtube video editor',
            'sort': 'relevance+desc',
            'highlight': True,
            'paging': {
                'offset': 0,
                'count': 10,
            },
        },
    },
}

response = requests.post('https://www.upwork.com/api/graphql/v1', params=params, cookies=cookies, headers=headers, json=json_data)

# Note: json_data will not be serialized by requests
# exactly as it was in the original request.
#data = '{"query":"\\n  query VisitorJobSearch($requestVariables: VisitorJobSearchV1Request!) {\\n    search {\\n      universalSearchNuxt {\\n        visitorJobSearchV1(request: $requestVariables) {\\n          paging {\\n            total\\n            offset\\n            count\\n          }\\n          \\n    facets {\\n      jobType \\n    {\\n      key\\n      value\\n    }\\n  \\n      workload \\n    {\\n      key\\n      value\\n    }\\n  \\n      clientHires \\n    {\\n      key\\n      value\\n    }\\n  \\n      durationV3 \\n    {\\n      key\\n      value\\n    }\\n  \\n      amount \\n    {\\n      key\\n      value\\n    }\\n  \\n      contractorTier \\n    {\\n      key\\n      value\\n    }\\n  \\n      contractToHire \\n    {\\n      key\\n      value\\n    }\\n  \\n      \\n    }\\n  \\n          results {\\n            id\\n            title\\n            description\\n            relevanceEncoded\\n            ontologySkills {\\n              uid\\n              parentSkillUid\\n              prefLabel\\n              prettyName: prefLabel\\n              freeText\\n              highlighted\\n            }\\n            \\n            jobTile {\\n              job {\\n                id\\n                ciphertext: cipherText\\n                jobType\\n                weeklyRetainerBudget\\n                hourlyBudgetMax\\n                hourlyBudgetMin\\n                hourlyEngagementType\\n                contractorTier\\n                sourcingTimestamp\\n                createTime\\n                publishTime\\n                \\n                hourlyEngagementDuration {\\n                  rid\\n                  label\\n                  weeks\\n                  mtime\\n                  ctime\\n                }\\n                fixedPriceAmount {\\n                  isoCurrencyCode\\n                  amount\\n                }\\n                fixedPriceEngagementDuration {\\n                  id\\n                  rid\\n                  label\\n                  weeks\\n                  ctime\\n                  mtime\\n                }\\n              }\\n            }\\n          }\\n        }\\n      }\\n    }\\n  }\\n  ","variables":{"requestVariables":{"userQuery":"youtube video editor","sort":"relevance+desc","highlight":true,"paging":{"offset":0,"count":10}}}}'
#response = requests.post('https://www.upwork.com/api/graphql/v1', params=params, cookies=cookies, headers=headers, data=data)