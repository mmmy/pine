#!/bin/bash

# Pine Script策略生成器打包脚本
# 功能：将schedule文件夹打包成压缩包，便于分发和备份

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${CYAN}=================================================${NC}"
    echo -e "${CYAN}    Pine Script策略生成器打包工具${NC}"
    echo -e "${CYAN}=================================================${NC}"
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    if ! command -v tar &> /dev/null; then
        print_error "tar命令未找到，请安装tar工具"
        print_info "Ubuntu/Debian: sudo apt-get install tar"
        print_info "CentOS/RHEL: sudo yum install tar"
        print_info "macOS: tar is pre-installed"
        exit 1
    fi
    
    print_success "tar工具已安装"
}

# 主函数
main() {
    print_header
    
    # 检查依赖
    check_dependencies
    
    # 设置变量 - 根据当前目录决定源文件夹
    if [ -d "schedule" ]; then
        SOURCE_DIR="schedule"
        print_info "检测到schedule文件夹，将打包schedule目录"
    elif [ -f "generate_strategy.ps1" ]; then
        SOURCE_DIR="."
        print_info "当前在schedule目录内，将打包当前目录"
    else
        print_error "未找到schedule文件夹或generate_strategy.ps1文件"
        print_info "请在包含schedule文件夹的目录或schedule目录内运行此脚本"
        exit 1
    fi
    OUTPUT_FILE="pine_script_strategy_generator.tar.gz"
    TEMP_DIR="temp_package_$$"
    
    print_info "源文件夹: $SOURCE_DIR"
    print_info "输出文件: $OUTPUT_FILE"
    
    # 删除旧的压缩包
    if [ -f "$OUTPUT_FILE" ]; then
        print_info "删除旧的压缩包: $OUTPUT_FILE"
        rm -f "$OUTPUT_FILE"
        print_success "旧压缩包已删除"
    else
        print_info "未发现旧压缩包"
    fi
    
    # 检查源文件夹是否存在
    if [ ! -d "$SOURCE_DIR" ]; then
        print_error "源文件夹 '$SOURCE_DIR' 不存在"
        exit 1
    fi
    
    print_success "源文件夹存在"
    
    # 创建临时目录
    print_info "创建临时打包目录..."
    mkdir -p "$TEMP_DIR/pine_script_strategy_generator"
    
    # 复制文件到临时目录（排除临时目录本身）
    print_info "复制文件到临时目录..."
    if [ "$SOURCE_DIR" = "." ]; then
        # 当前目录，需要排除临时目录（已删除旧tar.gz文件）
        find . -maxdepth 1 -type f ! -name "temp_package_*" -exec cp {} "$TEMP_DIR/pine_script_strategy_generator/" \;
        find . -maxdepth 1 -type d ! -name "." ! -name "temp_package_*" ! -name ".claude" -exec cp -r {} "$TEMP_DIR/pine_script_strategy_generator/" \;
    else
        # 指定目录，直接复制
        cp -r "$SOURCE_DIR"/* "$TEMP_DIR/pine_script_strategy_generator/"
    fi
    
    # 显示将要打包的文件
    print_info "将要打包的文件列表:"
    echo -e "${YELLOW}$(ls -la "$TEMP_DIR/pine_script_strategy_generator/")${NC}"
    
    # 计算文件数量和大小
    FILE_COUNT=$(find "$TEMP_DIR/pine_script_strategy_generator" -type f | wc -l)
    TOTAL_SIZE=$(du -sh "$TEMP_DIR/pine_script_strategy_generator" | cut -f1)
    
    print_info "文件数量: $FILE_COUNT 个"
    print_info "总大小: $TOTAL_SIZE"
    
    # 创建压缩包
    print_info "正在创建tar.gz压缩包..."
    cd "$TEMP_DIR"
    
    if tar -czf "../$OUTPUT_FILE" "pine_script_strategy_generator/" > /dev/null 2>&1; then
        cd ..
        print_success "压缩包创建成功: $OUTPUT_FILE"
    else
        cd ..
        print_error "压缩包创建失败"
        cleanup
        exit 1
    fi
    
    # 显示压缩包信息
    if [ -f "$OUTPUT_FILE" ]; then
        ARCHIVE_SIZE=$(du -sh "$OUTPUT_FILE" | cut -f1)
        print_info "压缩包大小: $ARCHIVE_SIZE"
        print_info "压缩包路径: $(pwd)/$OUTPUT_FILE"
        
        # 验证压缩包
        print_info "验证压缩包完整性..."
        if tar -tzf "$OUTPUT_FILE" > /dev/null 2>&1; then
            print_success "压缩包完整性验证通过"
        else
            print_warning "压缩包可能有问题，建议重新打包"
        fi
        
        # 显示压缩包内容
        print_info "压缩包内容预览:"
        echo -e "${YELLOW}$(tar -tzf "$OUTPUT_FILE" | head -20)${NC}"
        
        if [ $(tar -tzf "$OUTPUT_FILE" | wc -l) -gt 20 ]; then
            print_info "... (更多文件请使用 'tar -tzf $OUTPUT_FILE' 查看)"
        fi
    fi
    
    # 清理临时文件
    cleanup
    
    # 显示完成信息
    print_header
    print_success "打包完成！"
    print_info "压缩包文件: $OUTPUT_FILE"
    print_info "文件数量: $FILE_COUNT"
    print_info "原始大小: $TOTAL_SIZE"
    print_info "压缩后大小: $ARCHIVE_SIZE"
    print_info "压缩包路径: $(pwd)/$OUTPUT_FILE"
    
    # 提供使用建议
    echo ""
    print_info "使用建议:"
    echo -e "  ${CYAN}• 解压命令: tar -xzf $OUTPUT_FILE${NC}"
    echo -e "  ${CYAN}• 查看内容: tar -tzf $OUTPUT_FILE${NC}"
    echo -e "  ${CYAN}• 测试压缩包: tar -tzf $OUTPUT_FILE > /dev/null${NC}"
    
    # 询问是否要测试解压
    echo ""
    read -p "是否要测试解压压缩包？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_extraction
    fi
}

# 清理函数
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        print_info "清理临时文件..."
        rm -rf "$TEMP_DIR"
        print_success "临时文件清理完成"
    fi
}

# 测试解压函数
test_extraction() {
    print_info "测试解压功能..."
    TEST_DIR="test_extract_$$"
    mkdir -p "$TEST_DIR"
    
    cd "$TEST_DIR"
    if tar -xzf "../$OUTPUT_FILE"; then
        print_success "解压测试成功"
        print_info "解压后的文件结构:"
        echo -e "${YELLOW}$(tree pine_script_strategy_generator/ 2>/dev/null || find pine_script_strategy_generator/ -type f | head -10)${NC}"
    else
        print_error "解压测试失败"
    fi
    
    cd ..
    rm -rf "$TEST_DIR"
}

# 信号处理函数
handle_interrupt() {
    print_warning "接收到中断信号，正在清理..."
    cleanup
    exit 130
}

# 设置信号处理
trap handle_interrupt SIGINT SIGTERM

# 显示帮助信息
show_help() {
    echo "Pine Script策略生成器打包工具"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -v, --version  显示版本信息"
    echo ""
    echo "示例:"
    echo "  $0             # 打包schedule文件夹"
    echo "  $0 -h          # 显示帮助"
    echo ""
    echo "输出:"
    echo "  pine_script_strategy_generator.tar.gz"
    echo ""
}

# 显示版本信息
show_version() {
    echo "Pine Script策略生成器打包工具 v1.0"
    echo "作者: AI Assistant"
    echo "日期: 2025-07-08"
}

# 解析命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--version)
        show_version
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "未知选项: $1"
        show_help
        exit 1
        ;;
esac