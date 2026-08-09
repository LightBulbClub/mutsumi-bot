from core.config.decorator import on_module_config


@on_module_config("zzz")
class ZzzConfig:
    sched_energy_push: bool = True
    widget_resin: bool = True
    crazy_notice: bool = False
    refresh_bg: str = "bg2"
    zzz_guide_provide: str = "猫冬"
    refresh_card_use_pic: bool = True
    enable_custom_char_bg: bool = False
    refresh_data_list: list[str] = ["ENKA", "MINIGG", "MYS"]

