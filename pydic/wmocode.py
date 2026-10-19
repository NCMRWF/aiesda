WMO_DESCRIPTOR_TO_SUBTYPE = {
    # WMO_Code: (subtype_code, subtype_name, elemlist_key)
    
    # Category 00 [Table A Cat 0: Surface data - land / Table entries]
    300001: (10000, "table_entries", "elemlist_BASE"),

    # Category 01 [Table A Cat 0/1: Location and identification sequences]
    301001: (10001, "station_id", "elemlist_METADATA"),
    301002: (10002, "station_name", "elemlist_METADATA"),
    301011: (10011, "station_block", "elemlist_METADATA"),
    301012: (10012, "station_latlon", "elemlist_METADATA"),

    # Category 02 [Table A Cat 0/1: Surface common sequences]
    302001: (10101, "surface_header", "elemlist_SURFHEAD"),
    302002: (10102, "surface_pres_temp", "elemlist_SURFCOMMON"),

    # Category 03 [Table A Cat 2: Vertical soundings common sequences]
    303001: (50001, "sounding_header", "elemlist_SOUNDHEAD"),
    303002: (50002, "sounding_levels", "elemlist_SOUNDLVL"),

    # Category 04 [Table A Cat 3: Satellite observations common sequences]
    304001: (70001, "satellite_common", "elemlist_SATCOMMON"),

    # Category 05 [Table A Cat 13: Hydrological common sequences]
    305001: (60001, "hydrological_common", "elemlist_HYDROCOMMON"),

    # Category 06 [Table A Cat 31: Oceanographic common sequences]
    306001: (60201, "oceanographic_common", "elemlist_OCEANCOMMON"),

    # Category 07 [Table A Cat 0: Surface report sequences - land]
    307080: (10100, "landsynop", "elemlist_LNDSYB"),
    307081: (10100, "landsynop", "elemlist_LNDSYB"),
    307082: (10800, "mobsynop", "elemlist_MOBSYN"),
    307090: (11100, "metar", "elemlist_METARS"),
    307096: (10100, "landsynop", "elemlist_LNDSYB"), # SYNOP with Supplementary Information (GBON/AWS)

    # Category 08 [Table A Cat 1: Surface report sequences - sea]
    308001: (10200, "shipsynop", "elemlist_SHPSYN"),
    308002: (10300, "buoy", "elemlist_BUOY"),
    308003: (10300, "buoy", "elemlist_BUOYB"),
    308004: (10400, "rig", "elemlist_RIG"),
    308005: (10500, "platform", "elemlist_PLATFORM"),
    308009: (10900, "cman", "elemlist_CMAN"),

    # Category 09 [Table A Cat 2: Vertical sounding sequences - conventional]
    309050: (50100, "temp", "elemlist_TEMP"),
    309051: (50101, "tempship", "elemlist_TEMPSHIP"),
    309052: (50102, "radiosonde", "elemlist_RADIOSONDE"),
    309053: (50200, "pilot", "elemlist_PILOT"),
    309054: (50201, "pilotship", "elemlist_PILOTSHIP"),
    309055: (50400, "windprofiler", "elemlist_PROFILER"),

    # Category 10 [Table A Cat 3: Vertical sounding sequences - satellite]
    310001: (70101, "satsound_atovs", "elemlist_ATOVS"),
    310002: (70102, "satsound_tovs", "elemlist_TOVS"),
    310008: (70108, "satsound_airs_iasi", "elemlist_AIRSIASI"),
    310010: (70110, "satsound_cris", "elemlist_CRIS"),
    310070: (70170, "satsound_gnss_ro", "elemlist_GNSSRO"),

    # Category 11 [Table A Cat 4: Single level report sequences - conventional]
    311001: (30200, "aireps", "elemlist_AIREPS"),
    311002: (30201, "pireps", "elemlist_PIREPS"),
    311005: (30100, "amdars", "elemlist_AMDARS"),
    311009: (30109, "acars", "elemlist_ACARS"),

    # Category 12 [Table A Cat 5: Single level report sequences - satellite]
    312001: (70201, "satwind_amv", "elemlist_AMV"),
    312015: (70215, "scatterometer_ascat", "elemlist_ASCAT"),
    312020: (70220, "altimeter", "elemlist_ALTIMETER"),

    # Category 13 [Table A Cat 13: Image data common sequences]
    313001: (80001, "image_header", "elemlist_IMGHEAD"),
    313002: (80002, "image_calibration", "elemlist_IMGCAL"),

    # Category 14 [Table A Cat 14: Reserved / Unassigned]
    314000: (40100, "tcbogus", "elemlist_TCBOGUS"), # Retaining operational tropical cyclone bogus fallback
    314001: (40100, "tcbogus", "elemlist_TCBOGUS"),

    # Category 15 [Table A Cat 31: Oceanographic report sequences]
    315001: (60200, "tesac", "elemlist_TESAC"),
    315002: (60202, "xbt", "elemlist_XBT"),
    315003: (60203, "argo", "elemlist_ARGO"),
    315005: (60205, "tidegauge", "elemlist_TIDEGAUGE"),

    # Category 16 [Table A Cat 7: Synoptic feature sequences]
    316001: (40201, "cyclone_track", "elemlist_CYCLONE"),
    316002: (40202, "frontal_system", "elemlist_FRONT"),

    # Category 17 [Table A Cat 31: Oceanographic report sequences (extended)]
    317001: (60200, "tesac", "elemlist_TESAC"),
    317002: (60202, "xbt", "elemlist_XBT"),

    # Category 18 [Table A Cat 10: Radiological report sequences]
    318001: (90100, "radiological", "elemlist_RAD"),

    # Category 19 [Table A Cat 31: Oceanographic surface report sequences]
    319001: (60301, "surface_drifter", "elemlist_DRIFTER"),
    319002: (60302, "moored_buoy", "elemlist_MOORED"),

    # Category 20 [Table A Cat 13 / 20: Hydrological / Hydrographic data]
    320001: (60010, "river_stage", "elemlist_RIVER"),

    # Category 21 [Table A Cat 6: Radar report sequences]
    321001: (50501, "radar_header", "elemlist_RADARHEAD"),
    321002: (50502, "radar_wind", "elemlist_RADARWIND"),
    321003: (50503, "radar_reflectivity", "elemlist_RADARREF"),

    # Category 22 [Table A Cat 8: Chemical and aerosol sequences]
    322001: (90201, "ozone_profile", "elemlist_OZONE"),
    322002: (90202, "total_ozone", "elemlist_TOTOTOZONE"),
    322005: (90205, "aerosol", "elemlist_AEROSOL"),
    322008: (90208, "greenhouse_gas", "elemlist_GHG"),

    # Category 23 [Table A Cat 15: Agrometeorological data]
    323001: (10601, "soil_moisture", "elemlist_AGROMET"),

    # Categories 24 to 34 [Table A Satellites / Unassigned Blocks]
    324000: (79924, "reserved_unassigned", "elemlist_UNASSIGNED"),
    325001: (70301, "solar_radiation", "elemlist_SOLAR"),
    326000: (79926, "reserved_unassigned", "elemlist_UNASSIGNED"),
    327000: (79927, "reserved_unassigned", "elemlist_UNASSIGNED"),
    328001: (90301, "air_quality", "elemlist_AIRQUALITY"),
    329000: (79929, "reserved_unassigned", "elemlist_UNASSIGNED"),
    330000: (79930, "reserved_unassigned", "elemlist_UNASSIGNED"),
    331000: (79931, "reserved_unassigned", "elemlist_UNASSIGNED"),
    332000: (79932, "reserved_unassigned", "elemlist_UNASSIGNED"),
    333000: (79933, "reserved_unassigned", "elemlist_UNASSIGNED"),
    334000: (79934, "reserved_unassigned", "elemlist_UNASSIGNED"),

    # Category 35 [Table A: Monitoring information]
    335001: (99001, "monitoring_qc", "elemlist_QC"),

    # Categories 36 to 39 [Unassigned Blocks]
    336000: (79936, "reserved_unassigned", "elemlist_UNASSIGNED"),
    337000: (79937, "reserved_unassigned", "elemlist_UNASSIGNED"),
    338000: (79938, "reserved_unassigned", "elemlist_UNASSIGNED"),
    339000: (79939, "reserved_unassigned", "elemlist_UNASSIGNED"),

    # Category 40 [Table A Cat 101: Additional satellite report sequences]
    340001: (70401, "sat_additional", "elemlist_SATADD"),

    # Categories 41 to 47 [Unassigned Blocks]
    341000: (79941, "reserved_unassigned", "elemlist_UNASSIGNED"),
    342000: (79942, "reserved_unassigned", "elemlist_UNASSIGNED"),
    343000: (79943, "reserved_unassigned", "elemlist_UNASSIGNED"),
    344000: (79944, "reserved_unassigned", "elemlist_UNASSIGNED"),
    345000: (79945, "reserved_unassigned", "elemlist_UNASSIGNED"),
    346000: (79946, "reserved_unassigned", "elemlist_UNASSIGNED"),
    347000: (79947, "reserved_unassigned", "elemlist_UNASSIGNED"),

    # Categories 48 to 63 [Local / Regional implementation blocks]
    348000: (89948, "local_block_48", "elemlist_LOCAL"),
    349000: (89949, "local_block_49", "elemlist_LOCAL"),
    350000: (89950, "local_block_50", "elemlist_LOCAL"),
    351000: (89951, "local_block_51", "elemlist_LOCAL"),
    352000: (89952, "local_block_52", "elemlist_LOCAL"),
    353000: (89953, "local_block_53", "elemlist_LOCAL"),
    354000: (89954, "local_block_54", "elemlist_LOCAL"),
    355000: (89955, "local_block_55", "elemlist_LOCAL"),
    356000: (89956, "local_block_56", "elemlist_LOCAL"),
    357000: (89957, "local_block_57", "elemlist_LOCAL"),
    358000: (89958, "local_block_58", "elemlist_LOCAL"),
    359000: (89959, "local_block_59", "elemlist_LOCAL"),
    360000: (89960, "local_block_60", "elemlist_LOCAL"),
    361000: (89961, "local_block_61", "elemlist_LOCAL"),
    362000: (89962, "local_block_62", "elemlist_LOCAL"),
    363000: (89963, "local_block_63", "elemlist_LOCAL"),
}
