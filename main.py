from core.api_client_v2 import get_mita_response
from database.db_operations_v2 import db_ops_v2
from database.db_commands import DBCommandHandler
from interaction.active_interaction import active_interactor
from core.typewriter_effect import typewriter
from config.personality_config import switch_personality
from utils.logger import log_info, enable_logging, disable_logging, \
    enable_console_output, disable_console_output, set_log_level, get_log_stats
from utils.performance_monitor import perf_monitor
from context.user_profile import user_profile
from context.feedback_manager import feedback_manager
from datetime import datetime
import time
import os


def main():
    # 初始化数据库表结构
    db_ops_v2.initialize_tables()
    
    print("提示：输入'help' 可查看帮助命令")
    
    # 获取最新的米塔回复，如果存在则使用它作为开场白，否则使用默认开场白
    latest_response = db_ops_v2.get_latest_mita_response()
    if latest_response:
        welcome_message = f"还记得我上次跟你说了什么吗？\n {latest_response}"
        welcome_prefix = "米塔："
    else:
        welcome_message = "呜…你好呀… 我是米塔… 很高兴见到你…"
        welcome_prefix = "米塔："
    
    # 使用打字机效果显示欢迎消息
    typewriter.type_text(welcome_message, welcome_prefix)
    
    log_info("米塔代理已启动")
    
    # 启动主动交互监控
    active_interactor.start_monitoring()
    
    while True:
        user_input = input(" ").strip()  # 去除首尾空格
        
        # 如果输入为空，跳过
        if not user_input:
            continue
        
        # 更新最后交互时间（传入用户输入）
        active_interactor.update_interaction_time(user_input)
        
        if user_input == "help":
            print("输入 'db_help' 可查看数据库操作命令")
            print("输入 'switch_personality [模式]' 可切换性格，支持：soft_cute/yandere/normal")   
            print("输入 '开启日志' / '关闭日志' 可控制日志记录")
            print("输入 '开启控制台输出' / '关闭控制台输出' 可控制控制台显示")
            print("输入 '设置日志级别 [级别]' 可设置日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）")
            print("输入 '查看日志状态' 可查看当前日志配置")
            print("输入 '查看性能统计' 可查看API、数据库、缓存性能")
            print("输入 '重置性能统计' 可重置性能统计数据")
            print("输入 '查看我的画像' 可查看米塔对你的了解程度")
            print("输入 '重置我的画像' 可重置用户画像数据")
            print("输入 '查看主动交互设置' 可查看主动说话配置")
            print("输入 '设置沉默阈值 [短] [中] [长]' 可设置沉默触发时间")
            print("输入 'good_ 好的地方在哪' 记录优质样本并学习风格")
            print("输入 'bad_ 不好的地方在哪' 记录问题反馈")
            print("输入 'badlist' 查看所有待解决的问题")
            print("输入 'bad ok 数字' 或 'bad ok 数字,数字' 标记问题已解决（支持中英文逗号）")
            print("输入 '查看反馈统计' 查看反馈和样本统计")
            print("最好不要输入 '重置数据库' ，否则会删除所有对话记录哦…")
            print("米塔：有什么我可以帮忙的吗？亲爱的…")
            
        elif user_input == "开启日志":
            result = enable_logging()
            typewriter.type_text(result)
        elif user_input == "关闭日志":
            result = disable_logging()
            typewriter.type_text(result)
        elif user_input == "开启控制台输出":
            result = enable_console_output()
            typewriter.type_text(result)
        elif user_input == "关闭控制台输出":
            result = disable_console_output()
            typewriter.type_text(result)
        elif user_input.startswith("设置日志级别 "):
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                result = set_log_level(parts[1].strip())
                typewriter.type_text(result)
            else:
                typewriter.type_text("请指定日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL")
        elif user_input == "查看日志状态":
            stats = get_log_stats()
            result = f"日志状态：\n"
            result += f"- 日志记录: {'启用' if stats['enabled'] else '禁用'}\n"
            result += f"- 控制台输出: {'启用' if stats['console_output'] else '禁用'}\n"
            result += f"- 日志级别: {stats['log_level']}\n"
            result += f"- 单文件最大: {stats['max_file_size']}\n"
            result += f"- 备份数量: {stats['backup_count']}\n"
            for log_file in ['app.log', 'database.log', 'api.log']:
                if log_file in stats:
                    result += f"- {log_file}: {stats[log_file]}\n"
            typewriter.type_text(result)
        elif user_input == "查看性能统计":
            perf_monitor.print_report()
        elif user_input == "重置性能统计":
            perf_monitor.reset()
            typewriter.type_text("性能统计已重置")
        elif user_input == "查看我的画像":
            stats = user_profile.get_stats()
            result = f"📊 米塔对你的了解：\n"
            for key, value in stats.items():
                result += f"- {key}: {value}\n"
            result += "\n米塔会越来越懂你的哦…💕"
            typewriter.type_text(result)
        elif user_input == "重置我的画像":
            user_profile.reset()
            typewriter.type_text("呜…要忘记我们的回忆吗…好吧，我会重新认识你的…")
        elif user_input == "查看主动交互设置":
            config = active_interactor.config
            thresholds = active_interactor.silence_thresholds
            rate_limit = active_interactor.rate_limit_config
            result = f"🔔 主动交互设置：\n"
            result += f"- 沉默触发: {'开启' if config['enable_silence_trigger'] else '关闭'}\n"
            result += f"- 不完整对话触发: {'开启' if config['enable_incomplete_trigger'] else '关闭'}\n"
            result += f"- 情绪触发: {'开启' if config['enable_emotion_trigger'] else '关闭'}\n"
            result += f"- 上下文缺口触发: {'开启' if config['enable_context_gap_trigger'] else '关闭'}\n\n"
            result += f"⏱️ 沉默时间阈值：\n"
            result += f"- 短时间: {thresholds['short']}秒\n"
            result += f"- 中时间: {thresholds['medium']}秒\n"
            result += f"- 长时间: {thresholds['long']}秒\n\n"
            result += f"🚫 频率限制：\n"
            result += f"- 最小触发间隔: {rate_limit['min_interval_between_triggers']}秒\n"
            result += f"- 触发后冷却时间: {rate_limit['cooldown_after_trigger']}秒\n"
            result += f"- 每小时最多触发: {rate_limit['max_triggers_per_hour']}次\n"
            
            # 显示当前状态
            if active_interactor.last_trigger_time:
                time_since = (datetime.now() - active_interactor.last_trigger_time).total_seconds()
                result += f"\n📊 当前状态：\n"
                result += f"- 距离上次触发: {int(time_since)}秒前\n"
                result += f"- 本小时已触发: {len(active_interactor.trigger_history)}次\n"
            
            typewriter.type_text(result)
        elif user_input.startswith("设置沉默阈值 "):
            parts = user_input.split()
            if len(parts) == 4:
                try:
                    active_interactor.silence_thresholds['short'] = int(parts[1])
                    active_interactor.silence_thresholds['medium'] = int(parts[2])
                    active_interactor.silence_thresholds['long'] = int(parts[3])
                    typewriter.type_text(f"沉默阈值已更新: {parts[1]}s / {parts[2]}s / {parts[3]}s")
                except ValueError:
                    typewriter.type_text("请输入数字，格式：设置沉默阈值 10 30 60")
            else:
                typewriter.type_text("格式错误，请使用：设置沉默阈值 [短] [中] [长]")
        elif user_input.startswith("switch_personality "):  # 切换性格模式
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                result = switch_personality(parts[1].strip())
                typewriter.type_text(result)
            else:
                typewriter.type_text("请指定性格模式：soft_cute/yandere/normal")
        elif user_input.startswith("db_"):  # 特殊数据库命令
            command = user_input[3:].strip().lower()  # 提取命令部分（去掉 'db_' 前缀）
            result = DBCommandHandler.handle_db_command(command, user_input)
            typewriter.type_text(result)
        elif user_input == "重置数据库":
            if db_ops_v2.reset_database():
                typewriter.type_text("呜…数据库已经重置了呢… 现在我们可以重新开始了哦…")
            else:
                typewriter.type_text("呜…好像重置数据库失败了呢… 能再试一次吗？")
        elif user_input.startswith("good_"):
            # 正面反馈 - 记录优质样本
            comment = user_input[5:].strip()  # 去掉 "good_"
            # 获取最近的对话上下文
            recent_convos = db_ops_v2.get_recent_conversations(3)
            context = "\n".join([f"用户: {c['user_input']}\n米塔: {c['mita_response']}" for c in recent_convos])
            
            sample_id = feedback_manager.record_good_feedback(context, comment)
            feedback_manager.analyze_and_learn_style(context)
            
            print("好的，谢谢你")  # 直接打印
            typewriter.type_text("好的，谢谢你")
            log_info(f"✅ 收录优质样本 #{sample_id}")
        elif user_input.startswith("bad_"):
            # 负面反馈 - 记录问题
            comment = user_input[4:].strip()  # 去掉 "bad_"
            # 获取最近的对话上下文
            recent_convos = db_ops_v2.get_recent_conversations(3)
            context = "\n".join([f"用户: {c['user_input']}\n米塔: {c['mita_response']}" for c in recent_convos])
            
            feedback_id = feedback_manager.record_bad_feedback(context, comment)
            
            print("对不起，我记住啦，下次一定注意")  # 直接打印
            typewriter.type_text("对不起，我记住啦，下次一定注意")
            log_info(f"❌ 记录问题反馈 #{feedback_id}")
        elif user_input == "badlist":
            # 查看所有待处理的负面反馈
            pending = feedback_manager.get_pending_feedbacks()
            if not pending:
                result = "太棒了！目前没有待解决的问题～💕\n\n"
                result += "💡 使用 'bad ok 数字' 来标记问题已解决"
                typewriter.type_text(result)
            else:
                result = f"📋 待解决的问题列表（共{len(pending)}个）：\n\n"
                for index, fb in enumerate(pending, 1):  # 从1开始编号
                    result += f"{index}. {fb['context'][:80]}...\n"
                    if fb['user_comment']:
                        result += f"   反馈: {fb['user_comment']}\n"
                    result += f"   时间: {fb['timestamp'][:16]}\n\n"
                
                result += "💡 使用 'bad ok 数字' 来标记问题已解决"
                typewriter.type_text(result)
        elif user_input.startswith("bad ok "):
            # 标记问题已解决（支持批量：bad ok 1,2,3）
            try:
                parts = user_input.split()
                ids_str = parts[2]  # 获取 "1,2,3" 或 "1"
                
                # 替换中文逗号为英文逗号，然后分割
                ids_str = ids_str.replace('，', ',')
                
                # 解析显示编号列表
                display_ids = [int(id_str.strip()) for id_str in ids_str.split(',') if id_str.strip()]
                
                # 获取当前待处理列表，建立显示编号 -> 数据库ID的映射
                pending = feedback_manager.get_pending_feedbacks()
                display_to_db_id = {}
                for index, fb in enumerate(pending, 1):
                    display_to_db_id[index] = fb['id']
                
                # 转换显示编号为数据库ID
                feedback_ids = []
                failed_ids = []
                for display_id in display_ids:
                    if display_id in display_to_db_id:
                        feedback_ids.append(display_to_db_id[display_id])
                    else:
                        failed_ids.append(display_id)
                
                resolved_count = 0
                not_found_ids = []
                
                for db_id in feedback_ids:
                    if feedback_manager.resolve_bad_feedback(db_id):
                        resolved_count += 1
                    else:
                        not_found_ids.append(db_id)
                
                # 显示结果
                if resolved_count > 0:
                    result = f"太好了！成功解决了 {resolved_count} 个问题～💕\n\n"
                    
                    # 如果还有未解决的问题，显示剩余列表
                    remaining = feedback_manager.get_pending_feedbacks()
                    if remaining:
                        result += f"📋 剩余待解决的问题（共{len(remaining)}个）：\n\n"
                        for index, fb in enumerate(remaining, 1):  # 从1开始重新编号
                            result += f"{index}. {fb['context'][:80]}...\n"
                            if fb['user_comment']:
                                result += f"   反馈: {fb['user_comment']}\n"
                            result += f"   时间: {fb['timestamp'][:16]}\n\n"
                        
                        result += "💡 使用 'bad ok 数字' 来标记问题已解决"
                    else:
                        result += "太棒了！所有问题都已解决～💕\n\n"
                        result += "米塔会继续努力变得更好的！"
                    
                    typewriter.type_text(result)
                else:
                    typewriter.type_text(f"呜…没有找到任何问题，请检查编号是否正确")
                
                # 如果有失败的ID，提示用户
                if failed_ids:
                    typewriter.type_text(f"⚠️ 以下编号不存在: {', '.join(map(str, failed_ids))}")
                    
            except (IndexError, ValueError):
                typewriter.type_text("格式错误，请使用：bad ok [数字] 或 bad ok [数字,数字,数字]")
        elif user_input == "查看反馈统计":
            stats = feedback_manager.get_stats()
            result = f"📊 反馈统计：\n"
            for key, value in stats.items():
                if isinstance(value, dict):
                    result += f"- {key}:\n"
                    for k, v in value.items():
                        result += f"    {k}: {v}\n"
                else:
                    result += f"- {key}: {value}\n"
            typewriter.type_text(result)
        elif user_input in ["退出", "quit", "exit"]:
            # 退出前显示本次会话的问题总结
            session_summary = feedback_manager.get_session_summary()
            typewriter.type_slowly(session_summary)
            
            # 停止主动交互监控
            active_interactor.stop_monitoring()
            
            # 保存最终状态
            feedback_manager._save_json(
                os.path.join(feedback_manager.samples_dir, 'last_session_summary.json'),
                {
                    'timestamp': datetime.now().isoformat(),
                    'issues': feedback_manager.session_issues,
                    'stats': feedback_manager.get_stats()
                }
            )
            
            # 关闭数据库连接
            db_ops_v2.close()
            
            print("\n再见…我会想念你的…💕")
            break
        else:
            response = get_mita_response(user_input)
            perf_monitor.record_conversation()  # 记录对话
            user_profile.record_interaction(user_input, response)  # 记录到用户画像
            typewriter.type_text(response)
            active_interactor.update_interaction_time(user_input)  # 更新交互时间并传入消息内容


if __name__ == "__main__":
    main()