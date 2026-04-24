import sys
import os

# 添加项目根目录到路径，支持直接运行此文件
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_operations import db_ops
import re


class DBCommandHandler:
    """处理数据库命令的类"""
    
    @staticmethod
    def handle_db_command(command, user_input):
        """处理数据库命令"""
        # 查看所有对话记录
        if command == "view_all":
            conversations = db_ops.get_all_conversations()
            if conversations:
                result = f"共有 {len(conversations)} 条对话记录：\n\n"
                for conv in conversations:
                    result += f"ID: {conv['id']} | 时间: {conv['created_at']}\n用户: {conv['user_input']}\n米塔: {conv['mita_response']}\n{'-'*40}\n"
            else:
                result = "暂无对话记录。"
            return result

        # 查看最新对话记录
        elif command.startswith("view_latest"):
            parts = command.split("_")
            if len(parts) >= 3:
                try:
                    num = int(parts[2])
                except ValueError:
                    num = 5  # 默认查看5条
            else:
                num = 5  # 默认查看5条
            conversations = db_ops.get_latest_conversations(num)
            if conversations:
                result = f"最近 {len(conversations)} 条对话记录：\n\n"
                for conv in conversations:
                    result += f"ID: {conv['id']} | 时间: {conv['created_at']}\n用户: {conv['user_input']}\n米塔: {conv['mita_response']}\n{'-'*40}\n"
            else:
                result = "暂无对话记录。"
            return result

        # 删除特定对话记录
        elif command.startswith("delete_"):
            try:
                parts = command.split("_")
                conv_id = int(parts[1])  # 获取ID
                if db_ops.delete_conversation(conv_id):
                    return f"ID为 {conv_id} 的对话记录已删除。"
                else:
                    return f"删除ID为 {conv_id} 的对话记录失败。"
            except (ValueError, IndexError):
                return "删除命令格式错误，请使用: delete_[ID] 格式。例如: delete_5"

        # 更新特定对话记录
        elif command.startswith("update_"):
            try:
                parts = command.split("_", 2)
                conv_id = int(parts[1])  # 获取ID
                new_content = parts[2] if len(parts) > 2 else ""
                if new_content:
                    if db_ops.update_conversation(conv_id, mita_response=new_content):
                        return f"ID为 {conv_id} 的对话记录已更新。新内容: {new_content}"
                    else:
                        return f"更新ID为 {conv_id} 的对话记录失败。"
                else:
                    return "更新命令格式错误，缺少新内容。格式: update_[ID]_[新内容]。例如: update_5_这是新回复内容"
            except (ValueError, IndexError):
                return "更新命令格式错误，请使用: update_[ID]_[新内容] 格式。例如: update_5_这是新回复内容"

        # 获取对话总数
        elif command == "count":
            count = db_ops.get_conversation_count()
            return f"当前数据库中共有 {count} 条对话记录。"

        # 显示帮助
        elif command == "help":
            help_text = (
                "数据库操作命令列表：\n"
                "- db_view_all: 查看所有对话记录\n"
                "- db_view_latest_5: 查看最新的5条对话记录\n"
                "- db_delete_[ID]: 删除指定ID的对话记录\n"
                "- db_update_[ID]_[内容]: 更新对话记录\n"
                "- db_count: 查看对话总数\n"
                "- db_help: 显示此帮助\n"
                "- db_reset_db: 清空所有记录"
            )
            print(help_text)  # 直接打印，确保能看到
            return help_text

        # 重置数据库
        elif command == "reset_db":
            if db_ops.reset_database():
                return "数据库已重置，所有对话记录已被清空。"
            else:
                return "重置数据库失败。"

        else:
            return "未知的数据库命令，请输入 'db_help' 查看可用命令。"