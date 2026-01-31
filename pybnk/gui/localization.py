from dataclasses import dataclass


@dataclass
class Localization:
    language: str = "English"
    title: str = "ERSoundbankHelper"
    
    # Menu items
    menu_language: str = "Language"
    
    # Source bank section
    select_source_tooltip: str = "Select the soundbank your sounds are coming from"
    source_bank_label: str = "Source Soundbank"
    source_bank_path: str = ""
    
    # Destination bank section
    select_dest_tooltip: str = "Select the soundbank you want to copy the sounds to"
    dest_bank_label: str = "Destination Soundbank"
    dest_bank_path: str = ""
    
    # Wwise IDs section
    source_ids_tooltip: str = "The wwise IDs to copy from the source soundbank. Each line represents one entry and must follow the format 'xYYYY...'."
    source_ids_label: str = "Source Wwise IDs"
    source_wwise_ids: str = ""
    
    dest_ids_tooltip: str = "How the copied sounds will be named in the destination soundbank. Each line represents one entry and must follow the format 'xYYYY...'."
    dest_ids_label: str = "Destination Wwise IDs"
    dest_wwise_ids: str = ""
    
    # Tool buttons
    open_id_dialog_button: str = "Select IDs..."
    open_hash_dialog_button: str = "Calculate Hash"
    
    # Transfer button
    transfer_button: str = "Transfer"
    
    # Hash calculator dialog
    calc_hash_window: str = "Calculate Hash"
    calc_hash_input: str = "Input"
    calc_hash_output: str = "Hash"
    
    # ID lookup dialog
    select_source_first: str = "Select a source soundbank first"
    select_ids_tooltip: str = "This will only show events for which the hashes are known. You may still enter events manually even if they are not listed here."
    select_ids_window: str = "Select IDs"
    available_ids_label: str = "Available Source IDs"
    add_selected_button: str = "Add Selected >>"
    loading_ids: str = "Loading IDs..."
    
    # File dialog
    openfile_source_bank: str = "Select source soundbank.json"
    openfile_dest_bank: str = "Select destination soundbank.json"
    soundbank: str = "Soundbank files"
    json_files: str = "JSON files"
    all_files: str = "All files"
    
    # General UI
    no_file_selected: str = "No file selected"
    browse: str = "Browse"
    write_to_dest: str = "Write to destination"
    no_questions: str = "No questions"
    info_text: str = 'This tool allows you to transfer sounds from one soundbank to another. Streamed sounds are not handled (yet). If you see errors that some sounds could not be found, search for them in the game\'s "sd/wem" folder and copy them manually.'
    
    # Progress/Loading
    loading_dialog_title: str = "Please Wait"
    loading_dialog_message: str = "Processing..."
    transferring_sounds: str = "Transferring sounds..."
    
    # Success/Error messages
    transfer_successful: str = "Transfer successful"
    yay: str = "Yay!"
    transfer_failed: str = "Transfer failed"
    error: str = "Error"
    error_source_not_set: str = "Source soundbank not set"
    error_source_folder_not_exist: str = "Source soundbank folder does not exist"
    error_dest_not_set: str = "Destination soundbank not set"
    error_dest_folder_not_exist: str = "Destination soundbank folder does not exist"
    error_no_lines: str = "No lines were specified"
    error_line_mismatch: str = "Number of lines did not match"

    def __getitem__(self, key: str) -> str:
        return getattr(self, key, key)


@dataclass
class English(Localization):
    pass


@dataclass
class Chinese(English):
    language: str = "中文"
    title: str = "艾尔登法环音效迁移助手"
    
    # Menu items
    menu_language: str = "语言"
    
    # Source bank section
    select_source_tooltip: str = "选择您要从中提取音效的 soundbank"
    source_bank_label: str = "源 Soundbank"
    
    # Destination bank section
    select_dest_tooltip: str = "选择您要将音效复制到的 soundbank"
    dest_bank_label: str = "目标 Soundbank"
    
    # Wwise IDs section
    source_ids_tooltip: str = "要从源 soundbank 复制的 Wwise ID。每行一个，格式必须为 'xYYYY...'。"
    source_ids_label: str = "源 Wwise ID"
    
    dest_ids_tooltip: str = "复制后的音效在目标 soundbank 中的新名称。每行一个，格式必须为 'xYYYY...'。"
    dest_ids_label: str = "目标 Wwise ID"
    
    # Tool buttons
    open_id_dialog_button: str = "选择ID..."
    open_hash_dialog_button: str = "计算哈希值"
    
    # Transfer button
    transfer_button: str = "开始转移"
    
    # Hash calculator dialog
    calc_hash_window: str = "计算哈希值"
    calc_hash_input: str = "输入"
    calc_hash_output: str = "哈希值"
    
    # ID lookup dialog
    select_source_first: str = "请先选择源音频库"
    select_ids_tooltip: str = "此处仅显示已被rewwise映射哈希值的事件。您仍可手动输入此处未列出的任何事件。"
    select_ids_window: str = "选择ID"
    available_ids_label: str = "可用源 ID 列表"
    add_selected_button: str = "添加选中项 >>"
    loading_ids: str = "正在加载ID..."
    
    # File dialog
    openfile_source_bank: str = "选择源 soundbank.json"
    openfile_dest_bank: str = "选择目标 soundbank.json"
    soundbank: str = "Soundbank 文件"
    json_files: str = "JSON 文件"
    all_files: str = "所有文件"
    
    # General UI
    no_file_selected: str = "未选择文件"
    browse: str = "浏览"
    write_to_dest: str = "写入到目标文件"
    no_questions: str = "不进行询问（自动确认）"
    info_text: str = '本工具可将音效从一个 soundbank 转移到另一个。流式音效（Streamed sounds）暂不支持。如果遇到错误提示某些音效未找到，请在游戏的 "sd/wem" 文件夹中搜索它们并手动复制。'
    
    # Progress/Loading
    loading_dialog_title: str = "请稍候"
    loading_dialog_message: str = "处理中..."
    transferring_sounds: str = "正在转移音效..."
    
    # Success/Error messages
    transfer_successful: str = "转移成功"
    yay: str = "完成！"
    transfer_failed: str = "转移失败"
    error: str = "错误"
    error_source_not_set: str = "未设置源 soundbank"
    error_source_folder_not_exist: str = "源 soundbank 文件夹不存在"
    error_dest_not_set: str = "未设置目标 soundbank"
    error_dest_folder_not_exist: str = "目标 soundbank 文件夹不存在"
    error_no_lines: str = "未指定任何 ID"
    error_line_mismatch: str = "两侧 ID 的行数不匹配"