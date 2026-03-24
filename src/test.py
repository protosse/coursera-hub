from coursera_dl.coursera_dl import main_f as m

cmd = [
    # "--specialization",
    "fashion-silhouettes-icons",
    "--download-quizzes",
    "--download-notebooks",
    "--disable-url-skipping",
    "--unrestricted-filenames",
    "--combined-section-lectures-nums",
    "--jobs",
    "2",
    "--cauth",
    "52Mqyz756nKYLElgoEPJj_gBpJbw7qvGiGmE9MAWTtI7_l05neIiQ8YV_YolGK1nmst0y0llQKPB44hkESmgCA.sCYMGYnqMllqkHTXrFvd-Q._hFqNImgwGFzUenS3YssEiV98ZiuoUW-muTnd9GbD8uJ2LqUPLX-8ADdu929VDjPFYsaFfdW1a1XgXZPvyF7HeXxSUeoX7Ml1If9EdC1PAqzDTG9mdQmftGhP6Q9VaWFlXIOsA0FU9ZTc98nu7L6Bl7k_C-RUFxj7HQ0JAbyGqH90le065HydJ_HE2S75NQIC4c6l-mtb_2m8ABZaDJe467ZRZQF1cC-iJ65JEwIff2_LHEDZ6X-z9Mg4N9y6YCeTqDbOc4LcL3_10fyaUa2WKgueJPsfbS9TrtVh64Aobkb1HJ6qKH3MrVCDwpSibXADNDatVxEKbUcRh2D-is8ewk6LDT8uQKfirmPeVEM6314KM9voP51JhIMPAsPWpuEMzotjLaRrzgDZCGBESf6eN2ORMOjb6E1kwhAx3T769MSL4xIMI1LJ-7j889lgDH9sf2o5z3BhIzwmXOD14T9F6HFek7F3WBF6cd0OEYB3Ho",
    "--subtitle-language",
    "en,zh-CN|zh-TW",
    "--video-resolution",
    "720p",
    "--download-delay",
    "10",
    "--cache-syllabus",
    "--aria2",
]

try:
    m(cmd)
except Exception as e:
    print(f"发生错误：{e}")
