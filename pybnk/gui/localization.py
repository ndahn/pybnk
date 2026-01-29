from dataclasses import dataclass


@dataclass
class Localization:
    language = "English"
    title = "ERSoundbankHelper"
    select_source_tooltip = "Select the soundbank your sounds are coming from"
    source_soundbank_label = "Source Soundbank:"
    no_file_selected = "No file selected"
    browse = "Browse"
    select_dest_tooltip = "Select the soundbank you want to copy the sounds to"
    dest_soundbank_label = "Destination Soundbank:"
    source_ids_tooltip = "The wwise IDs to copy from the source soundbank. Each line represents one entry and must follow the format 'xYYYY...'."
    source_ids_label = "Source Wwise IDs"
    dest_ids_tooltip = "How the copied sounds will be named in the destination soundbank. Each line represents one entry and must follow the format 'xYYYY...'."
    dest_ids_label = "Destination Wwise IDs"
    write_to_dest = "Write to destination"
    no_questions = "No questions"
    info_text = 'This tool allows you to transfer sounds from one soundbank to another. Streamed sounds are not handled (yet). If you see errors that some sounds could not be found, search for them in the game\'s "sd/wem" folder and copy them manually.',
    transfer_button = "Transfer"
    loading_dialog_title = "Please Wait"
    loading_dialog_message = "Processing..."
    transferring_sounds = "Transferring sounds..."
    transfer_successful = "Transfer successful"
    yay = "Yay!"
    transfer_failed = "Transfer failed"
    error = "Error"
    value_error_source_not_set = "Source soundbank not set"
    value_error_source_folder_not_exist = "Source soundbank folder does not exist"
    value_error_dest_not_set = "Destination soundbank not set"
    value_error_dest_folder_not_exist = "Destination soundbank folder does not exist"
    value_error_no_lines = "No lines were specified"
    value_error_line_mismatch = "Number of lines did not match"
    select_source_json = "Select source soundbank.json"
    select_dest_json = "Select destination soundbank.json"
    json_files = "JSON files"
    all_files = "All files"
    open_id_dialog_button = "Select IDs..."
    select_source_first = "Select a source soundbank first"
    select_ids_tooltip = "This will only show events for which the hashes are known. You may still enter events manually even if they are not listed here."
    select_ids_dialog_title = "Select IDs"
    available_ids_label = "Available Source IDs:"
    add_selected_button = "Add Selected >>"
    loading_ids = "Loading IDs..."

    def __getitem__(self, key: str) -> str:
        return getattr(self, key, key)


@dataclass
class English(Localization):
    pass


@dataclass
class Chinese(Localization):
    language = "Chinese"
    title = "艾尔登法环音效迁移助手"
    select_source_tooltip = "选择您要从中提取音效的 soundbank"
    source_soundbank_label = "源 Soundbank:"
    no_file_selected = "未选择文件"
    browse = "浏览"
    select_dest_tooltip = "选择您要将音效复制到的 soundbank"
    dest_soundbank_label = "目标 Soundbank:"
    source_ids_tooltip = "要从源 soundbank 复制的 Wwise ID。每行一个，格式必须为 'xYYYY...'。"
    source_ids_label = "源 Wwise ID"
    dest_ids_tooltip = "复制后的音效在目标 soundbank 中的新名称。每行一个，格式必须为 'xYYYY...'。"
    dest_ids_label = "目标 Wwise ID"
    write_to_dest = "写入到目标文件"
    no_questions = "不进行询问（自动确认）"
    info_text = '本工具可将音效从一个 soundbank 转移到另一个。流式音效（Streamed sounds）暂不支持。如果遇到错误提示某些音效未找到，请在游戏的 "sd/wem" 文件夹中搜索它们并手动复制。',
    transfer_button = "开始转移"
    loading_dialog_title = "请稍候"
    loading_dialog_message = "处理中..."
    transferring_sounds = "正在转移音效..."
    transfer_successful = "转移成功"
    yay = "完成！"
    transfer_failed = "转移失败"
    error = "错误"
    value_error_source_not_set = "未设置源 soundbank"
    value_error_source_folder_not_exist = "源 soundbank 文件夹不存在"
    value_error_dest_not_set = "未设置目标 soundbank"
    value_error_dest_folder_not_exist = "目标 soundbank 文件夹不存在"
    value_error_no_lines = "未指定任何 ID"
    value_error_line_mismatch = "两侧 ID 的行数不匹配"
    select_source_json = "选择源 soundbank.json"
    select_dest_json = "选择目标 soundbank.json"
    json_files = "JSON 文件"
    all_files = "所有文件"
    open_id_dialog_button = "选择ID..."
    select_source_first = "请先选择源音频库"
    select_ids_tooltip = "此处仅显示已被rewwise映射哈希值的事件。您仍可手动输入此处未列出的任何事件。"
    select_ids_dialog_title = "选择ID"
    available_ids_label = "可用源 ID 列表:"
    add_selected_button = "添加选中项 >>"
    loading_ids = "正在加载ID..."
