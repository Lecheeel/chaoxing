/**
 * 超星学习通自动签到系统 - 前端主要JavaScript文件
 */

// 全局变量
let toastContainer = null;
let loadingToast = null;

// 初始化函数
$(document).ready(function() {
    initializeApp();
    setupGlobalEventListeners();
    initializeToastContainer();
});

/**
 * 初始化应用
 */
function initializeApp() {
    // 初始化工具提示
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // 初始化弹出框
    if (typeof bootstrap !== 'undefined' && bootstrap.Popover) {
        var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
    
    // 添加页面加载动画
    $('body').addClass('fade-in');
}

/**
 * 设置全局事件监听器
 */
function setupGlobalEventListeners() {
    // 全局Ajax错误处理
    $(document).ajaxError(function(event, xhr, options, error) {
        console.error('Ajax Error:', error);
        if (xhr.status === 403) {
            showToast('权限不足', 'error');
        } else if (xhr.status === 500) {
            showToast('服务器内部错误', 'error');
        } else if (xhr.status === 0) {
            showToast('网络连接失败', 'error');
        }
    });
    
    // 表单提交增强
    $('form').on('submit', function(e) {
        const $form = $(this);
        const $submitBtn = $form.find('button[type="submit"]');
        
        // 防止重复提交
        if ($submitBtn.hasClass('loading')) {
            e.preventDefault();
            return false;
        }
        
        // 添加加载状态
        $submitBtn.addClass('loading').prop('disabled', true);
        
        // 2秒后恢复按钮状态（防止卡死）
        setTimeout(() => {
            $submitBtn.removeClass('loading').prop('disabled', false);
        }, 2000);
    });
    
    // 导航栏活动状态
    updateNavbarActiveState();
}

/**
 * 初始化Toast容器
 */
function initializeToastContainer() {
    if (!$('.toast-container').length) {
        $('body').append(`
            <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 1055; top: 70px !important;">
            </div>
        `);
    }
    toastContainer = $('.toast-container');
}

/**
 * 显示Toast消息
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, error, warning, info)
 * @param {number} duration - 显示时长（毫秒）
 */
function showToast(message, type = 'info', duration = 3000) {
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-triangle',
        warning: 'fa-exclamation-circle',
        info: 'fa-info-circle'
    };
    
    const colorMap = {
        success: 'text-success',
        error: 'text-danger',
        warning: 'text-warning',
        info: 'text-info'
    };
    
    const toastId = 'toast_' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="fas ${iconMap[type]} ${colorMap[type]} me-2"></i>
                    <span>${message}</span>
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.append(toastHtml);
    
    const toastElement = $(`#${toastId}`)[0];
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });
    
    toast.show();
    
    // 自动移除DOM元素
    setTimeout(() => {
        $(`#${toastId}`).remove();
    }, duration + 500);
}

/**
 * 显示加载Toast
 * @param {string} message - 加载消息
 */
function showLoadingToast(message = '加载中...') {
    const toastId = 'loading_toast';
    
    // 移除现有的加载Toast
    $(`#${toastId}`).remove();
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span>${message}</span>
                </div>
            </div>
        </div>
    `;
    
    toastContainer.append(toastHtml);
    
    const toastElement = $(`#${toastId}`)[0];
    loadingToast = new bootstrap.Toast(toastElement, {
        autohide: false
    });
    
    loadingToast.show();
}

/**
 * 隐藏加载Toast
 */
function hideLoadingToast() {
    if (loadingToast) {
        loadingToast.hide();
        setTimeout(() => {
            $('#loading_toast').remove();
            loadingToast = null;
        }, 300);
    }
}

/**
 * 警告对话框（替换原生alert）
 * @param {string} message - 警告消息
 * @param {string} title - 对话框标题
 * @param {string} type - 对话框类型 (info, warning, error, success)
 * @returns {Promise<void>}
 */
function alertDialog(message, title = '提示', type = 'info') {
    return new Promise((resolve) => {
        const modalId = 'alertModal_' + Date.now();
        
        const iconMap = {
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle',
            error: 'fa-times-circle',
            success: 'fa-check-circle'
        };
        
        const colorMap = {
            info: 'text-info',
            warning: 'text-warning',
            error: 'text-danger',
            success: 'text-success'
        };
        
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas ${iconMap[type]} ${colorMap[type]} me-2"></i>${title}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="mb-0">${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">确定</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        const modal = new bootstrap.Modal($(`#${modalId}`)[0]);
        
        $(`#${modalId}`).on('hidden.bs.modal', function() {
            $(`#${modalId}`).remove();
            resolve();
        });
        
        modal.show();
    });
}

/**
 * 确认对话框
 * @param {string} message - 确认消息
 * @param {string} title - 对话框标题
 * @returns {Promise<boolean>} - 用户选择结果
 */
function confirmDialog(message, title = '确认操作') {
    return new Promise((resolve) => {
        const modalId = 'confirmModal_' + Date.now();
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-question-circle me-2"></i>${title}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <p class="mb-0">${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="confirmBtn">确认</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        const modal = new bootstrap.Modal($(`#${modalId}`)[0]);
        
        let resolved = false;
        
        $(`#${modalId} #confirmBtn`).on('click', function() {
            if (!resolved) {
                resolved = true;
                modal.hide();
                resolve(true);
            }
        });
        
        $(`#${modalId}`).on('hidden.bs.modal', function() {
            $(`#${modalId}`).remove();
            if (!resolved) {
                resolved = true;
                resolve(false);
            }
        });
        
        modal.show();
    });
}

/**
 * 格式化日期时间
 * @param {string|Date} date - 日期
 * @param {string} format - 格式
 * @returns {string} - 格式化后的日期字符串
 */
function formatDateTime(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!date) return '--';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return '--';
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

/**
 * 获取相对时间
 * @param {string|Date} date - 日期
 * @returns {string} - 相对时间字符串
 */
function getRelativeTime(date) {
    if (!date) return '--';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return '--';
    
    const now = new Date();
    const diff = now - d;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    return '刚刚';
}

/**
 * 更新导航栏活动状态
 */
function updateNavbarActiveState() {
    const currentPath = window.location.pathname;
    
    // 移除所有活动状态
    $('.navbar-nav .nav-link').removeClass('active');
    
    // 根据当前路径设置活动状态
    $('.navbar-nav .nav-link').each(function() {
        const link = $(this);
        const href = link.attr('href');
        
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.addClass('active');
        }
    });
    
    // 处理首页
    if (currentPath === '/') {
        $('.navbar-nav .nav-link[href="/"]').addClass('active');
    }
}

/**
 * 数字格式化
 * @param {number} num - 数字
 * @returns {string} - 格式化后的数字
 */
function formatNumber(num) {
    if (num === null || num === undefined) return '--';
    if (typeof num !== 'number') return num;
    return num.toLocaleString();
}

/**
 * 文件大小格式化
 * @param {number} bytes - 字节数
 * @returns {string} - 格式化后的文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    if (!bytes) return '--';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 百分比格式化
 * @param {number} value - 数值
 * @param {number} total - 总数
 * @returns {string} - 百分比字符串
 */
function formatPercentage(value, total) {
    if (!value || !total) return '0%';
    return Math.round((value / total) * 100) + '%';
}

/**
 * 复制文本到剪贴板
 * @param {string} text - 要复制的文本
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('已复制到剪贴板', 'success');
        }).catch(err => {
            console.error('复制失败:', err);
            showToast('复制失败', 'error');
        });
    } else {
        // 兼容旧浏览器
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showToast('已复制到剪贴板', 'success');
        } catch (err) {
            console.error('复制失败:', err);
            showToast('复制失败', 'error');
        }
        document.body.removeChild(textArea);
    }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间
 * @returns {Function} - 防抖后的函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 限制时间
 * @returns {Function} - 节流后的函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 检查网络连接
 */
function checkNetworkConnection() {
    if (navigator.onLine) {
        $('#status-indicator').removeClass('bg-danger').addClass('bg-success').text('运行中');
    } else {
        $('#status-indicator').removeClass('bg-success').addClass('bg-danger').text('离线');
    }
}

// 监听网络状态变化
window.addEventListener('online', checkNetworkConnection);
window.addEventListener('offline', checkNetworkConnection);

/**
 * 页面可见性变化处理
 */
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // 页面不可见时的处理
        console.log('页面隐藏');
    } else {
        // 页面可见时的处理
        console.log('页面显示');
        checkNetworkConnection();
    }
});

/**
 * 滚动到顶部
 */
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 添加返回顶部按钮
$(window).scroll(function() {
    if ($(this).scrollTop() > 300) {
        if (!$('#backToTop').length) {
            $('body').append(`
                <button id="backToTop" class="btn btn-primary position-fixed" 
                        style="bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 50px; height: 50px;"
                        onclick="scrollToTop()" title="返回顶部">
                    <i class="fas fa-arrow-up"></i>
                </button>
            `);
        }
        $('#backToTop').fadeIn();
    } else {
        $('#backToTop').fadeOut();
    }
});

/**
 * 加载状态管理
 */
class LoadingManager {
    constructor() {
        this.loadingCount = 0;
    }
    
    show(message = '加载中...') {
        this.loadingCount++;
        if (this.loadingCount === 1) {
            showLoadingToast(message);
        }
    }
    
    hide() {
        this.loadingCount = Math.max(0, this.loadingCount - 1);
        if (this.loadingCount === 0) {
            hideLoadingToast();
        }
    }
}

// 全局加载管理器
window.loadingManager = new LoadingManager();

// 导出常用函数到全局作用域
window.showToast = showToast;
window.showLoadingToast = showLoadingToast;
window.hideLoadingToast = hideLoadingToast;
window.alertDialog = alertDialog;
window.confirmDialog = confirmDialog;
window.formatDateTime = formatDateTime;
window.getRelativeTime = getRelativeTime;
window.formatNumber = formatNumber;
window.formatFileSize = formatFileSize;
window.formatPercentage = formatPercentage;
window.copyToClipboard = copyToClipboard;
window.debounce = debounce;
window.throttle = throttle; 