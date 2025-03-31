// 全局变量
let users = [];
let currentSelectedUser = null;
let userPresets = {};
let monitors = []; // 监控状态列表

// 编辑定时任务
let currentEditTaskId = null;

// 使用jQuery而非原生JS来处理DOM加载完成事件
$(document).ready(function() {
    console.log('DOM已通过jQuery加载完成');
    
    // 加载用户数据
    loadUsers();
    
    // 加载位置预设
    loadLocationPresets();
    
    // 加载定时任务列表
    loadScheduleTasks();
    
    // 加载监控状态列表
    loadMonitors();
    
    // 加载用户选项到选择框
    loadUserOptions();
    
    // 绑定事件
    $('#addUserBtn').on('click', addUser);
    $('#saveUserBtn').on('click', saveUser);
    $('#batchSignBtn').on('click', function() {
        console.log('批量签到按钮被jQuery点击');
        batchSign();
    });
    $('#userSelect').on('change', userSelectChanged);
    $('#addLocationBtn').on('click', addLocationPreset);
    $('#batchSetLocationBtn').on('click', showBatchSetLocationModal);
    $('#saveBatchLocationBtn').on('click', saveBatchLocation);
    $('#togglePassword').on('click', togglePassword);
    $('#toggleCurrentPassword').on('click', toggleCurrentPassword);
    
    // 监控管理相关事件
    $('#stopAllMonitorsBtn').on('click', stopAllMonitors);
    $('#startMonitorBtn').on('click', startMonitor);
    $('#refreshMonitorsBtn').on('click', function() {
        showToast('正在刷新监控状态...', 'info');
        loadMonitors();
    });
    
    // 设置定时刷新监控状态 (每30秒刷新一次)
    setInterval(loadMonitors, 30000);
    
    // 设置导航链接功能
    $('.navbar-nav .nav-link').on('click', function() {
        $('.navbar-nav .nav-link').removeClass('active');
        $(this).addClass('active');
    });
    
    // 切换任务类型显示相应设置
    $('#scheduleType').change(function() {
        const type = $(this).val();
        
        // 隐藏所有设置区域
        $('#timeSettings, #weekSettings, #intervalSettings').addClass('d-none');
        
        if (type === 'daily') {
            $('#timeSettings').removeClass('d-none');
        } else if (type === 'weekly') {
            $('#timeSettings, #weekSettings').removeClass('d-none');
        } else if (type === 'interval') {
            $('#intervalSettings').removeClass('d-none');
        }
    });
    
    $('#editScheduleType').change(function() {
        const type = $(this).val();
        
        // 隐藏所有设置区域
        $('#editTimeSettings, #editWeekSettings, #editIntervalSettings').addClass('d-none');
        
        if (type === 'daily') {
            $('#editTimeSettings').removeClass('d-none');
        } else if (type === 'weekly') {
            $('#editTimeSettings, #editWeekSettings').removeClass('d-none');
        } else if (type === 'interval') {
            $('#editIntervalSettings').removeClass('d-none');
        }
    });
    
    // 用户选择方式切换
    $('#scheduleUserType').change(function() {
        const type = $(this).val();
        
        if (type === 'phone') {
            $('#userPhoneSelect').removeClass('d-none');
            $('#userIndexInput').addClass('d-none');
        } else {  // index
            $('#userPhoneSelect').addClass('d-none');
            $('#userIndexInput').removeClass('d-none');
        }
    });
    
    // 编辑模态框中的用户选择方式切换
    $('#editScheduleUserType').change(function() {
        const type = $(this).val();
        
        if (type === 'phone') {
            $('#editUserPhoneSelect').removeClass('d-none');
            $('#editUserIndexInput').addClass('d-none');
        } else {  // index
            $('#editUserPhoneSelect').addClass('d-none');
            $('#editUserIndexInput').removeClass('d-none');
        }
    });
    
    // 位置选择切换
    $('#scheduleLocation').change(function() {
        const value = $(this).val();
        
        if (value === 'custom') {
            $('#customLocationSettings').removeClass('d-none');
        } else {
            $('#customLocationSettings').addClass('d-none');
        }
    });
    
    $('#editScheduleLocation').change(function() {
        const value = $(this).val();
        
        if (value === 'custom') {
            $('#editCustomLocationSettings').removeClass('d-none');
        } else {
            $('#editCustomLocationSettings').addClass('d-none');
        }
    });
    
    // 保存定时任务
    $('#saveScheduleBtn').click(function() {
        // 收集表单数据
        const formData = {
            name: $('#scheduleName').val(),
            type: $('#scheduleType').val(),
            user_type: $('#scheduleUserType').val(),
            active: true
        };
        
        // 验证必填字段
        if (!formData.name || !formData.type || !formData.user_type) {
            showToast('请填写所有必填字段', 'error');
            return;
        }
        
        // 根据任务类型添加字段
        if (formData.type === 'daily' || formData.type === 'weekly') {
            formData.time = $('#scheduleTime').val();
            
            if (!formData.time) {
                showToast('请选择执行时间', 'error');
                return;
            }
            
            if (formData.type === 'weekly') {
                // 收集选中的星期
                const days = [];
                $('.weekday:checked').each(function() {
                    days.push(parseInt($(this).val()));
                });
                
                if (days.length === 0) {
                    showToast('请选择至少一天', 'error');
                    return;
                }
                
                formData.days = days;
            }
        } else if (formData.type === 'interval') {
            formData.interval = parseInt($('#scheduleInterval').val());
            formData.unit = $('#scheduleUnit').val();
            
            if (!formData.interval) {
                showToast('请输入有效的间隔值', 'error');
                return;
            }
        }
        
        // 根据用户选择方式添加用户ID
        if (formData.user_type === 'phone') {
            // 获取选中的用户IDs
            const selectedUserIds = getSelectedUserIds('.user-checkbox');
            
            if (selectedUserIds.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            
            formData.user_ids = selectedUserIds;
        } else {
            const userIndex = $('#scheduleUserIndex').val();
            
            if (!userIndex && userIndex !== '0') {
                showToast('请输入有效的用户索引', 'error');
                return;
            }
            
            formData.user_ids = [userIndex];
        }
        
        // 处理位置参数
        const locationType = $('#scheduleLocation').val();
        
        if (locationType === 'custom') {
            // 获取自定义位置参数
            const address = $('#scheduleCustomAddress').val().trim();
            const lon = $('#scheduleCustomLon').val().trim();
            const lat = $('#scheduleCustomLat').val().trim();
            
            if (!address || !lon || !lat) {
                showToast('请填写完整的自定义位置信息', 'error');
                return;
            }
            
            // 添加自定义位置参数
            formData.location_address = address;
            formData.location_lon = parseFloat(lon);
            formData.location_lat = parseFloat(lat);
        } else if (locationType) {
            // 使用预设位置
            formData.location_preset_item = locationType;
        }
        
        formData.location_random_offset = $('#scheduleRandomOffset').is(':checked');
        
        // 发送请求
        axios.post('/api/schedule', formData)
            .then(function(response) {
                if (response.data.status) {
                    showToast('定时任务创建成功', 'success');
                    $('#addScheduleModal').modal('hide');
                    loadScheduleTasks();
                } else {
                    showToast('创建失败: ' + response.data.message, 'error');
                }
            })
            .catch(function(error) {
                console.error('创建定时任务失败:', error);
                showToast('创建定时任务失败', 'error');
            });
    });
    
    // 打开编辑任务模态框
    $(document).on('click', '.edit-schedule', function() {
        const taskId = $(this).closest('tr').data('id');
        
        // 加载任务数据
        editSchedule(taskId);
    });
    
    // 更新定时任务
    $('#updateScheduleBtn').click(function() {
        if (!currentEditTaskId) {
            showToast('任务ID无效', 'error');
            return;
        }
        
        // 收集表单数据
        const formData = {
            name: $('#editScheduleName').val(),
            type: $('#editScheduleType').val(),
            user_type: $('#editScheduleUserType').val(),
            active: $('#editScheduleActive').is(':checked')
        };
        
        // 验证必填字段
        if (!formData.name || !formData.type || !formData.user_type) {
            showToast('请填写所有必填字段', 'error');
            return;
        }
        
        // 根据任务类型添加字段
        if (formData.type === 'daily' || formData.type === 'weekly') {
            formData.time = $('#editScheduleTime').val();
            
            if (!formData.time) {
                showToast('请选择执行时间', 'error');
                return;
            }
            
            if (formData.type === 'weekly') {
                // 收集选中的星期
                const days = [];
                $('.editWeekday:checked').each(function() {
                    days.push(parseInt($(this).val()));
                });
                
                if (days.length === 0) {
                    showToast('请选择至少一天', 'error');
                    return;
                }
                
                formData.days = days;
            }
        } else if (formData.type === 'interval') {
            formData.interval = parseInt($('#editScheduleInterval').val());
            formData.unit = $('#editScheduleUnit').val();
            
            if (!formData.interval) {
                showToast('请输入有效的间隔值', 'error');
                return;
            }
        }
        
        // 根据用户选择方式添加用户ID
        if (formData.user_type === 'phone') {
            // 获取选中的用户IDs
            const selectedUserIds = getSelectedUserIds('.edit-user-checkbox');
            
            if (selectedUserIds.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            
            formData.user_ids = selectedUserIds;
        } else {
            const userIndex = $('#editScheduleUserIndex').val();
            
            if (!userIndex && userIndex !== '0') {
                showToast('请输入有效的用户索引', 'error');
                return;
            }
            
            formData.user_ids = [userIndex];
        }
        
        // 处理位置参数
        const locationType = $('#editScheduleLocation').val();
        
        if (locationType === 'custom') {
            // 获取自定义位置参数
            const address = $('#editScheduleCustomAddress').val().trim();
            const lon = $('#editScheduleCustomLon').val().trim();
            const lat = $('#editScheduleCustomLat').val().trim();
            
            if (!address || !lon || !lat) {
                showToast('请填写完整的自定义位置信息', 'error');
                return;
            }
            
            // 添加自定义位置参数
            formData.location_address = address;
            formData.location_lon = parseFloat(lon);
            formData.location_lat = parseFloat(lat);
            formData.location_preset_item = null;  // 清除预设项
        } else if (locationType) {
            // 使用预设位置
            formData.location_preset_item = locationType;
            // 清除自定义位置参数
            formData.location_address = null;
            formData.location_lon = null;
            formData.location_lat = null;
        } else {
            // 使用默认位置，清除所有位置参数
            formData.location_preset_item = null;
            formData.location_address = null;
            formData.location_lon = null;
            formData.location_lat = null;
        }
        
        formData.location_random_offset = $('#editScheduleRandomOffset').is(':checked');
        
        // 发送请求
        axios.put(`/api/schedule/${currentEditTaskId}`, formData)
            .then(function(response) {
                if (response.data.status) {
                    showToast('定时任务更新成功', 'success');
                    $('#editScheduleModal').modal('hide');
                    loadScheduleTasks();
                } else {
                    showToast('更新失败: ' + response.data.message, 'error');
                }
            })
            .catch(function(error) {
                console.error('更新定时任务失败:', error);
                showToast('更新定时任务失败', 'error');
            });
    });
    
    // 立即执行任务
    $(document).on('click', '.execute-schedule', function() {
        const taskId = $(this).data('id');
        executeSchedule(taskId);
    });
    
    // 删除任务
    $(document).on('click', '.delete-schedule', function() {
        const taskId = $(this).data('id');
        deleteSchedule(taskId);
    });
    
    // 每30秒自动刷新任务列表
    setInterval(loadScheduleTasks, 30000);
});

// 加载用户列表
function loadUsers() {
    showLoading('加载用户列表');
    
    axios.get('/api/users')
        .then(response => {
            if (response.data.status) {
                users = response.data.users;
                updateUserTable();
                updateUserSelect();
                loadLocationPresets();
                hideLoading();
            } else {
                hideLoading();
                showError('加载用户失败: ' + response.data.message);
            }
        })
        .catch(error => {
            console.error('获取用户数据出错:', error);
            hideLoading();
            showError('获取用户数据时发生错误: ' + (error.message || '未知错误'));
        });
}

// 更新用户表格
function updateUserTable() {
    // 获取表格元素
    const tableBody = document.querySelector('#userTable tbody');
    tableBody.innerHTML = '';
    
    // 如果没有用户，显示提示信息
    if (users.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="5" class="text-center text-muted py-4">暂无用户数据</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // 获取操作按钮和状态徽章模板
    const actionsTemplate = document.getElementById('userActionsTemplate').innerHTML;
    const statusTemplate = document.getElementById('userStatusTemplate').innerHTML;
    
    // 为每个用户创建表格行
    users.forEach(function(user, index) {
        const row = document.createElement('tr');
        
        // 创建状态徽章
        const statusBadge = document.createElement('div');
        statusBadge.innerHTML = statusTemplate;
        const badge = statusBadge.querySelector('.status-badge');
        badge.classList.add('badge');
        
        if (user.active) {
            badge.classList.add('bg-success');
            badge.textContent = '已激活';
        } else {
            badge.classList.add('bg-secondary');
            badge.textContent = '未激活';
        }
        
        // 设置表格内容
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${user.username || '<span class="text-muted">未知</span>'}</td>
            <td>${user.phone}</td>
            <td>${statusBadge.innerHTML}</td>
            <td>${actionsTemplate}</td>
        `;
        
        // 设置按钮事件
        const editBtn = row.querySelector('.edit-user');
        editBtn.addEventListener('click', function() {
            editUser(user.phone);
        });
        
        const toggleBtn = row.querySelector('.toggle-active');
        toggleBtn.addEventListener('click', function() {
            toggleUserActive(user.phone, !user.active);
        });
        
        const deleteBtn = row.querySelector('.delete-user');
        deleteBtn.addEventListener('click', function() {
            deleteUser(user.phone);
        });
        
        const signBtn = row.querySelector('.sign-user');
        signBtn.addEventListener('click', function() {
            signUser(user.phone);
        });
        
        // 添加监控按钮
        const monitorBtn = document.createElement('button');
        monitorBtn.className = 'btn btn-sm btn-info text-white monitor-user';
        monitorBtn.title = '启动监控';
        monitorBtn.innerHTML = '<i class="fas fa-eye"></i>';
        monitorBtn.addEventListener('click', function() {
            showStartMonitorModal(user.phone);
        });
        
        // 将监控按钮添加到操作组
        const actionGroup = row.querySelector('.btn-group');
        actionGroup.appendChild(monitorBtn);
        
        // 添加行到表格
        tableBody.appendChild(row);
    });
}

// 更新用户选择器
function updateUserSelect() {
    const select = document.getElementById('userSelect');
    
    // 保存当前选择
    const currentValue = select.value;
    
    // 清空选项
    while (select.options.length > 1) {
        select.remove(1);
    }
    
    // 添加用户选项
    users.forEach(user => {
        const option = document.createElement('option');
        option.value = user.phone;
        option.textContent = `${user.username || '未知用户'} (${user.phone})`;
        select.appendChild(option);
    });
    
    // 恢复选择
    if (currentValue) {
        select.value = currentValue;
    }
}

// 添加新用户
function addUser() {
    const phone = document.getElementById('phone').value.trim();
    const password = document.getElementById('password').value.trim();
    
    if (!phone || !password) {
        showError('请输入手机号和密码');
        return;
    }
    
    // 显示加载状态
    showLoading('添加用户');
    
    axios.post('/api/users', { phone, password })
        .then(response => {
            hideLoading();
            if (response.data.status) {
                // 重置表单并关闭模态框
                document.getElementById('addUserForm').reset();
                bootstrap.Modal.getInstance(document.getElementById('addUserModal')).hide();
                
                // 刷新用户列表
                loadUsers();
                
                showSuccess('用户添加成功');
            } else {
                showError(response.data.message);
            }
        })
        .catch(error => {
            console.error('添加用户出错:', error);
            hideLoading();
            showError('添加用户时发生错误: ' + (error.message || '未知错误'));
        });
}

// 编辑用户信息
function editUser(phone) {
    const user = users.find(u => u.phone === phone);
    if (!user) {
        showError('未找到该用户');
        return;
    }
    
    // 设置模态框数据
    document.getElementById('originalPhone').value = phone; // 保存原始手机号用于后续更新
    document.getElementById('editPhone').value = phone;
    document.getElementById('editUsername').value = user.username || '';
    
    // 设置当前密码
    const currentPasswordInput = document.getElementById('currentPassword');
    if (user.password) {
        currentPasswordInput.value = user.password;
        // 默认密码显示为掩码
        currentPasswordInput.type = 'password';
        document.querySelector('#toggleCurrentPassword i').className = 'fas fa-eye';
    } else {
        currentPasswordInput.value = '密码信息不可用';
    }
    
    document.getElementById('editPassword').value = '';
    
    // 明确设置激活状态开关，确保与用户状态一致
    const activeCheckbox = document.getElementById('editActive');
    // user.active 可能是 undefined、true 或 false，我们需要将 undefined 视为 true（默认激活）
    activeCheckbox.checked = user.active !== false;
    
    // 显示模态框
    new bootstrap.Modal(document.getElementById('editUserModal')).show();
}

// 保存编辑后的用户信息
function saveUser() {
    const originalPhone = document.getElementById('originalPhone').value;
    const newPhone = document.getElementById('editPhone').value.trim();
    const password = document.getElementById('editPassword').value.trim();
    const active = document.getElementById('editActive').checked;
    
    if (!newPhone) {
        showError('手机号不能为空');
        return;
    }
    
    // 构建要更新的数据
    const data = { 
        phone: newPhone,
        active: active // 确保active值被正确传递
    };
    
    if (password) {
        data.password = password;
    }
    
    // 显示加载状态
    showLoading('保存用户信息');
    
    axios.put(`/api/users/${originalPhone}`, data)
        .then(response => {
            hideLoading();
            if (response.data.status) {
                // 关闭模态框
                bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
                
                // 刷新用户列表
                loadUsers();
                
                showSuccess('用户信息更新成功');
            } else {
                showError(response.data.message);
            }
        })
        .catch(error => {
            console.error('更新用户出错:', error);
            hideLoading();
            showError('更新用户时发生错误: ' + (error.message || '未知错误'));
        });
}

// 删除用户
function deleteUser(phone) {
    Swal.fire({
        title: '确认删除',
        text: `确认要删除手机号为 ${phone} 的用户吗？`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        background: '#f8f9fa',
        customClass: {
            title: 'text-warning',
            confirmButton: 'btn btn-danger px-4',
            cancelButton: 'btn btn-secondary px-4',
            popup: 'swal-custom-popup'
        },
        showClass: {
            popup: 'swal2-show-custom',
            backdrop: 'swal2-backdrop-show',
            icon: 'swal2-icon-show'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            showLoading('删除用户');
            axios.delete(`/api/users/${phone}`)
                .then(response => {
                    hideLoading();
                    if (response.data.status) {
                        // 刷新用户列表
                        loadUsers();
                        
                        showSuccess('用户删除成功');
                    } else {
                        showError(response.data.message);
                    }
                })
                .catch(error => {
                    console.error('删除用户出错:', error);
                    hideLoading();
                    showError('删除用户时发生错误: ' + (error.message || '未知错误'));
                });
        }
    });
}

// 对单个用户进行签到
function signUser(phone) {
    Swal.fire({
        title: '确认签到',
        text: `确认要为手机号为 ${phone} 的用户执行签到吗？`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认签到',
        cancelButtonText: '取消',
        background: '#f8f9fa',
        customClass: {
            title: 'text-info',
            confirmButton: 'btn btn-success px-4',
            cancelButton: 'btn btn-secondary px-4',
            popup: 'swal-custom-popup'
        },
        showClass: {
            popup: 'swal2-show-custom'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // 获取签到设置
            const useRandomOffset = document.getElementById('useRandomOffset').checked;
            
            // 显示加载状态
            showLoading('执行签到');
            
            axios.post(`/api/sign/${phone}`, { location_random_offset: useRandomOffset })
                .then(response => {
                    hideLoading();
                    if (response.data.status) {
                        showSuccess(`用户 ${phone} 签到成功`);
                    } else {
                        showError(`用户 ${phone} 签到失败: ${response.data.message}`);
                    }
                })
                .catch(error => {
                    console.error('签到出错:', error);
                    hideLoading();
                    showError('签到时发生错误: ' + (error.message || '未知错误'));
                });
        }
    });
}

// 批量签到
function batchSign() {
    console.log('批量签到按钮被点击');
    
    Swal.fire({
        title: '批量签到',
        text: '确认要为所有用户执行批量签到吗？',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认签到',
        cancelButtonText: '取消',
        background: '#f8f9fa',
        customClass: {
            title: 'text-info',
            confirmButton: 'btn btn-success px-4',
            cancelButton: 'btn btn-secondary px-4',
            popup: 'swal-custom-popup'
        },
        showClass: {
            popup: 'swal2-show-custom'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            executeBatchSign();
        }
    });
}

// 执行批量签到逻辑
function executeBatchSign() {
    console.log('用户确认了批量签到操作');
    // 获取签到设置
    const excludeInactive = document.getElementById('excludeInactiveUsers').checked;
    const useRandomOffset = document.getElementById('useRandomOffset').checked;
    
    console.log('签到设置:', {excludeInactive, useRandomOffset});
    
    // 显示加载状态
    showLoading('批量签到中');
    
    // 清空结果区域
    const resultDiv = document.getElementById('batchSignResult');
    resultDiv.innerHTML = '';
    
    // 签到请求
    console.log('发送批量签到请求');
    axios.post('/api/sign/all', {
        exclude_inactive: excludeInactive,
        location_random_offset: useRandomOffset
    })
        .then(response => {
            console.log('批量签到响应:', response.data);
            hideLoading();
            if (response.data.status) {
                // 显示签到结果
                showBatchSignResults(response.data.results);
            } else {
                showError('批量签到失败: ' + response.data.message);
            }
        })
        .catch(function(error) {
            console.error('批量签到出错:', error);
            hideLoading();
            showError('批量签到时发生错误: ' + (error.message || '未知错误'));
        });
}

// 显示批量签到结果
function showBatchSignResults(results) {
    const resultDiv = document.getElementById('batchSignResult');
    resultDiv.innerHTML = '';
    
    if (!results || results.length === 0) {
        resultDiv.innerHTML = '<div class="alert alert-warning">没有用户需要签到</div>';
        return;
    }
    
    // 计算签到统计
    const total = results.length;
    const success = results.filter(r => r.status).length;
    const failed = total - success;
    
    // 创建结果卡片
    const card = document.createElement('div');
    card.className = 'card';
    
    // 卡片头部
    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header d-flex justify-content-between align-items-center';
    cardHeader.innerHTML = `
        <h5 class="mb-0"><i class="fas fa-clipboard-check me-2"></i>签到结果</h5>
        <div class="badge-group">
            <span class="badge bg-primary">总计: ${total}</span>
            <span class="badge bg-success">成功: ${success}</span>
            <span class="badge bg-danger">失败: ${failed}</span>
        </div>
    `;
    card.appendChild(cardHeader);
    
    // 卡片内容
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    // 创建表格
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover mb-0';
    table.innerHTML = `
        <thead class="table-light">
            <tr>
                <th>用户</th>
                <th>手机号</th>
                <th>状态</th>
                <th>消息</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    
    // 添加结果行
    const tbody = table.querySelector('tbody');
    results.forEach(result => {
        const tr = document.createElement('tr');
        tr.className = result.status ? '' : 'table-danger';
        tr.innerHTML = `
            <td>${result.name}</td>
            <td>${result.phone}</td>
            <td><span class="badge ${result.status ? 'bg-success' : 'bg-danger'}">${result.status ? '成功' : '失败'}</span></td>
            <td>${result.message}</td>
        `;
        tbody.appendChild(tr);
    });
    
    cardBody.appendChild(table);
    card.appendChild(cardBody);
    resultDiv.appendChild(card);
    
    // 滚动到结果区域
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

// 用户选择变更
function userSelectChanged() {
    const phone = document.getElementById('userSelect').value;
    if (!phone) {
        // 如果未选择用户，清空位置预设表格
        document.querySelector('#presetTable tbody').innerHTML = '';
        return;
    }
    
    currentSelectedUser = phone;
    updateLocationPresetTable(phone);
}

// 加载位置预设列表
function loadLocationPresets() {
    axios.get('/api/location/presets')
        .then(response => {
            if (response.data.status) {
                userPresets = response.data.presets;
                // 如果当前已选择用户，更新其位置预设表格
                if (currentSelectedUser) {
                    updateLocationPresetTable(currentSelectedUser);
                }
            } else {
                console.error('加载位置预设失败:', response.data.message);
            }
        })
        .catch(error => {
            console.error('获取位置预设出错:', error);
        });
}

// 更新位置预设表格
function updateLocationPresetTable(phone) {
    const tbody = document.querySelector('#presetTable tbody');
    tbody.innerHTML = '';
    
    if (!userPresets[phone] || !userPresets[phone].presets || userPresets[phone].presets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">未设置位置预设</td></tr>';
        return;
    }
    
    userPresets[phone].presets.forEach((preset, index) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${preset.address || '-'}</td>
            <td>${preset.lon || '-'}</td>
            <td>${preset.lat || '-'}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="deletePreset('${phone}', ${index})">删除</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// 添加位置预设
function addLocationPreset() {
    const phone = document.getElementById('userSelect').value;
    if (!phone) {
        showError('请先选择用户');
        return;
    }
    
    const address = document.getElementById('locationAddress').value.trim();
    const lon = document.getElementById('locationLon').value.trim();
    const lat = document.getElementById('locationLat').value.trim();
    
    if (!address || !lon || !lat) {
        showError('请填写完整的位置信息');
        return;
    }
    
    // 显示加载状态
    showLoading('添加位置预设');
    
    axios.post(`/api/location/presets/${phone}`, { address, lon, lat })
        .then(response => {
            hideLoading();
            if (response.data.status) {
                // 重置表单并关闭模态框
                document.getElementById('addLocationForm').reset();
                bootstrap.Modal.getInstance(document.getElementById('addLocationModal')).hide();
                
                // 刷新位置预设
                loadLocationPresets();
                
                showSuccess('位置预设添加成功');
            } else {
                showError(response.data.message);
            }
        })
        .catch(error => {
            console.error('添加位置预设出错:', error);
            hideLoading();
            showError('添加位置预设时发生错误: ' + (error.message || '未知错误'));
        });
}

// 删除位置预设
function deletePreset(phone, index) {
    Swal.fire({
        title: '确认删除',
        text: '确认要删除这个位置预设吗？',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        background: '#f8f9fa',
        customClass: {
            title: 'text-warning',
            confirmButton: 'btn btn-danger px-4',
            cancelButton: 'btn btn-secondary px-4',
            popup: 'swal-custom-popup'
        },
        showClass: {
            popup: 'swal2-show-custom'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // 显示加载状态
            showLoading('删除位置预设');
            
            // 调用删除API
            axios.delete(`/api/location/presets/${phone}/${index}`)
                .then(response => {
                    hideLoading();
                    if (response.data.status) {
                        // 刷新位置预设
                        loadLocationPresets();
                        
                        showSuccess('位置预设删除成功');
                    } else {
                        showError(response.data.message);
                    }
                })
                .catch(error => {
                    console.error('删除位置预设出错:', error);
                    hideLoading();
                    showError('删除位置预设时发生错误: ' + (error.message || '未知错误'));
                });
        }
    });
}

// 切换密码显示/隐藏
function togglePassword() {
    const passwordInput = document.getElementById('editPassword');
    const toggleBtn = document.getElementById('togglePassword');
    const icon = toggleBtn.querySelector('i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// 切换当前密码显示/隐藏
function toggleCurrentPassword() {
    const passwordInput = document.getElementById('currentPassword');
    const toggleBtn = document.getElementById('toggleCurrentPassword');
    const icon = toggleBtn.querySelector('i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        icon.className = 'fas fa-eye';
    }
}

// 显示批量设置位置模态框
function showBatchSetLocationModal() {
    const modal = new bootstrap.Modal(document.getElementById('batchSetLocationModal'));
    const userCheckboxesContainer = document.querySelector('#batchSetLocationModal .border');
    
    // 清空现有复选框
    userCheckboxesContainer.innerHTML = '';
    
    // 添加用户复选框
    users.forEach(user => {
        const div = document.createElement('div');
        div.className = 'form-check';
        div.innerHTML = `
            <input class="form-check-input" type="checkbox" value="${user.phone}" id="userCheck_${user.phone}">
            <label class="form-check-label" for="userCheck_${user.phone}">
                ${user.username || '未知用户'} (${user.phone})
            </label>
        `;
        userCheckboxesContainer.appendChild(div);
    });
    
    modal.show();
}

// 保存批量位置设置
function saveBatchLocation() {
    const address = document.getElementById('batchLocationAddress').value.trim();
    const lon = document.getElementById('batchLocationLon').value.trim();
    const lat = document.getElementById('batchLocationLat').value.trim();
    
    if (!address || !lon || !lat) {
        showError('请填写完整的位置信息');
        return;
    }
    
    // 获取选中的用户
    const selectedUsers = Array.from(document.querySelectorAll('#batchSetLocationModal input[type="checkbox"]:checked'))
        .map(checkbox => checkbox.value);
    
    if (selectedUsers.length === 0) {
        showError('请至少选择一个用户');
        return;
    }
    
    // 显示加载状态
    showLoading('批量设置位置');
    
    // 批量设置位置
    const promises = selectedUsers.map(phone => 
        axios.post(`/api/location/presets/${phone}`, { address, lon, lat })
    );
    
    Promise.all(promises)
        .then(results => {
            hideLoading();
            const success = results.filter(r => r.data.status).length;
            const total = results.length;
            
            // 关闭模态框
            bootstrap.Modal.getInstance(document.getElementById('batchSetLocationModal')).hide();
            
            // 刷新位置预设
            loadLocationPresets();
            
            // 显示结果
            showSuccess(`成功为 ${success}/${total} 个用户设置位置`);
        })
        .catch(error => {
            console.error('批量设置位置出错:', error);
            hideLoading();
            showError('批量设置位置时发生错误: ' + (error.message || '未知错误'));
        });
}

// 切换用户激活状态
function toggleUserActive(phone, isActive) {
    axios.put(`/api/users/${phone}`, { active: isActive })
        .then(response => {
            if (response.data.status) {
                // 更新本地用户数据
                const user = users.find(u => u.phone === phone);
                if (user) {
                    user.active = isActive;
                }
                
                // 更新表格行样式 - 添加DOM元素存在性检查
                const switchElement = document.querySelector(`#activeSwitch_${phone}`);
                if (switchElement) {
                    const tr = switchElement.closest('tr');
                    if (tr) {
                        if (isActive) {
                            tr.classList.remove('table-secondary');
                        } else {
                            tr.classList.add('table-secondary');
                        }
                    }
                    
                    // 更新标签文本和样式 - 添加DOM元素存在性检查
                    const nextElement = switchElement.nextElementSibling;
                    if (nextElement) {
                        const badge = nextElement.querySelector('.badge');
                        if (badge) {
                            badge.textContent = isActive ? '已激活' : '未激活';
                            badge.className = `badge ${isActive ? 'bg-success' : 'bg-secondary'}`;
                        }
                    }
                }
                
                // 在成功切换状态后刷新用户列表，确保UI一致性
                updateUserTable();
                showSuccess(`用户 ${phone} ${isActive ? '已激活' : '已停用'}`);
            } else {
                showError(response.data.message);
                // 回滚UI状态 - 添加DOM元素存在性检查
                const switchElement = document.querySelector(`#activeSwitch_${phone}`);
                if (switchElement) {
                    switchElement.checked = !isActive;
                }
            }
        })
        .catch(error => {
            console.error('更新用户状态出错:', error);
            showError('更新用户状态时发生错误: ' + (error.message || '未知错误'));
            // 回滚UI状态 - 添加DOM元素存在性检查
            const switchElement = document.querySelector(`#activeSwitch_${phone}`);
            if (switchElement) {
                switchElement.checked = !isActive;
            }
        });
}

// 辅助函数：显示加载中
function showLoading(text = '加载中') {
    Swal.fire({
        title: text,
        text: '请稍候...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        },
        background: '#f8f9fa',
        customClass: {
            title: 'text-primary',
            popup: 'swal-custom-popup'
        }
    });
}

// 辅助函数：隐藏加载中
function hideLoading() {
    Swal.close();
}

// 辅助函数：显示成功消息
function showSuccess(message) {
    Toastify({
        text: message,
        duration: 3000,
        gravity: "top",
        position: "right",
        style: {
            background: "linear-gradient(to right, #00b09b, #96c93d)",
            borderRadius: "8px",
            fontSize: "15px",
            padding: "12px 20px"
        },
        onClick: function(){}, // 点击关闭
        stopOnFocus: true,
        close: true,
        className: "toastify-custom"
    }).showToast();
}

// 辅助函数：显示错误消息
function showError(message) {
    Swal.fire({
        icon: 'error',
        title: '操作失败',
        text: message,
        confirmButtonColor: '#dc3545',
        background: '#f8f9fa',
        customClass: {
            title: 'text-danger',
            confirmButton: 'btn btn-danger px-4',
            popup: 'swal-custom-popup'
        },
        showClass: {
            popup: 'swal2-show-custom',
            backdrop: 'swal2-backdrop-show',
            icon: 'swal2-icon-show'
        },
        hideClass: {
            popup: 'swal2-hide',
            backdrop: 'swal2-backdrop-hide',
            icon: 'swal2-icon-hide'
        }
    });
}

// 渲染用户表格
function renderUserTable(users) {
    const tableBody = $('#userTable tbody');
    tableBody.empty();
    
    // 使用模板
    const actionTemplate = document.getElementById('userActionsTemplate');
    const statusTemplate = document.getElementById('userStatusTemplate');
    
    users.forEach((user, index) => {
        const row = $('<tr>');
        
        // ID列
        row.append($('<td>').text(index + 1));
        
        // 用户名列
        row.append($('<td>').text(user.username || '未知用户'));
        
        // 手机号列
        row.append($('<td>').text(user.phone));
        
        // 状态列 - 使用模板
        const statusCell = $('<td>');
        const statusBadge = $(statusTemplate.content.cloneNode(true)).find('.status-badge');
        
        if (user.active) {
            statusBadge.addClass('active').text('已激活');
        } else {
            statusBadge.addClass('inactive').text('未激活');
        }
        
        statusCell.append(statusBadge);
        row.append(statusCell);
        
        // 操作列 - 使用模板
        const actionCell = $('<td>');
        const actionButtons = $(actionTemplate.content.cloneNode(true));
        
        // 为按钮添加数据属性
        actionButtons.find('.edit-user').attr('data-phone', user.phone);
        actionButtons.find('.toggle-active').attr('data-phone', user.phone).attr('data-active', user.active);
        actionButtons.find('.delete-user').attr('data-phone', user.phone);
        actionButtons.find('.sign-user').attr('data-phone', user.phone);
        
        // 根据激活状态更改切换按钮样式
        if (!user.active) {
            actionButtons.find('.toggle-active')
                .removeClass('btn-warning')
                .addClass('btn-secondary');
        }
        
        actionCell.append(actionButtons);
        row.append(actionCell);
        
        tableBody.append(row);
    });
    
    // 绑定操作按钮事件
    $('#userTable .edit-user').click(function() {
        const phone = $(this).data('phone');
        openEditUserModal(phone);
    });
    
    $('#userTable .toggle-active').click(function() {
        const phone = $(this).data('phone');
        const currentActive = $(this).data('active');
        toggleUserActive(phone, !currentActive);
    });
    
    $('#userTable .delete-user').click(function() {
        const phone = $(this).data('phone');
        deleteUser(phone);
    });
    
    $('#userTable .sign-user').click(function() {
        const phone = $(this).data('phone');
        signUser(phone);
    });
}

/**
 * 显示浮动通知
 * @param {string} message - 通知消息
 * @param {string} type - 通知类型：success, error, warning, info
 */
function showToast(message, type = 'info') {
    let backgroundColor = '#1a73e8'; // 默认蓝色
    
    switch (type) {
        case 'success':
            backgroundColor = '#28a745';
            break;
        case 'error':
            backgroundColor = '#dc3545';
            break;
        case 'warning':
            backgroundColor = '#ffc107';
            break;
    }
    
    Toastify({
        text: message,
        duration: 3000,
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: backgroundColor,
        stopOnFocus: true,
    }).showToast();
}

// 加载用户列表到选择框
function loadUserOptions() {
    axios.get('/api/users')
        .then(function(response) {
            if (response.data.status && response.data.users) {
                const users = response.data.users;
                
                // 清空现有选项
                $('#userCheckboxes').empty();
                $('#editUserCheckboxes').empty();
                
                // 添加用户复选框
                users.forEach(function(user) {
                    const userPhone = user.phone;
                    const userName = user.username || '未知用户';
                    const isActive = user.active !== false;
                    
                    // 创建添加任务的复选框
                    const userCheckbox = `
                        <div class="form-check mb-2">
                            <input class="form-check-input user-checkbox" type="checkbox" value="${userPhone}" 
                                id="user_${userPhone}" ${isActive ? '' : 'disabled'}>
                            <label class="form-check-label" for="user_${userPhone}">
                                ${userName} (${userPhone}) ${isActive ? '' : '<span class="text-danger">[已禁用]</span>'}
                            </label>
                        </div>
                    `;
                    $('#userCheckboxes').append(userCheckbox);
                    
                    // 创建编辑任务的复选框
                    const editUserCheckbox = `
                        <div class="form-check mb-2">
                            <input class="form-check-input edit-user-checkbox" type="checkbox" value="${userPhone}" 
                                id="edit_user_${userPhone}" ${isActive ? '' : 'disabled'}>
                            <label class="form-check-label" for="edit_user_${userPhone}">
                                ${userName} (${userPhone}) ${isActive ? '' : '<span class="text-danger">[已禁用]</span>'}
                            </label>
                        </div>
                    `;
                    $('#editUserCheckboxes').append(editUserCheckbox);
                });
                
                // 全选/取消全选功能
                $('#selectAllUsers').on('change', function() {
                    const isChecked = $(this).prop('checked');
                    $('.user-checkbox:not([disabled])').prop('checked', isChecked);
                });
                
                $('#editSelectAllUsers').on('change', function() {
                    const isChecked = $(this).prop('checked');
                    $('.edit-user-checkbox:not([disabled])').prop('checked', isChecked);
                });
                
                // 当单个复选框更改时更新全选框状态
                $(document).on('change', '.user-checkbox', function() {
                    updateSelectAllCheckbox('#selectAllUsers', '.user-checkbox:not([disabled])');
                });
                
                $(document).on('change', '.edit-user-checkbox', function() {
                    updateSelectAllCheckbox('#editSelectAllUsers', '.edit-user-checkbox:not([disabled])');
                });
            }
        })
        .catch(function(error) {
            console.error('获取用户列表失败:', error);
            showToast('获取用户列表失败', 'error');
        });
}

// 更新全选复选框状态
function updateSelectAllCheckbox(selectAllId, checkboxSelector) {
    const totalCheckboxes = $(checkboxSelector).length;
    const checkedCheckboxes = $(checkboxSelector + ':checked').length;
    
    if (checkedCheckboxes === 0) {
        $(selectAllId).prop('checked', false);
        $(selectAllId).prop('indeterminate', false);
    } else if (checkedCheckboxes === totalCheckboxes) {
        $(selectAllId).prop('checked', true);
        $(selectAllId).prop('indeterminate', false);
    } else {
        $(selectAllId).prop('indeterminate', true);
    }
}

// 获取选中的用户ID
function getSelectedUserIds(checkboxSelector) {
    const selectedUserIds = [];
    $(checkboxSelector + ':checked').each(function() {
        selectedUserIds.push($(this).val());
    });
    return selectedUserIds;
}

// 加载定时任务列表
function loadScheduleTasks() {
    axios.get('/api/schedule')
        .then(function(response) {
            if (response.data.status) {
                displayScheduleTasks(response.data.tasks);
            } else {
                showToast('获取定时任务失败: ' + response.data.message, 'error');
            }
        })
        .catch(function(error) {
            console.error('获取定时任务失败:', error);
            showToast('获取定时任务失败', 'error');
        });
}

// 显示定时任务列表
function displayScheduleTasks(tasks) {
    const tbody = $('#scheduleTable tbody');
    tbody.empty();

    if (!tasks || tasks.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="8" class="text-center">暂无定时任务</td>
            </tr>
        `);
        return;
    }

    tasks.forEach(task => {
        // 构建任务类型和执行时间显示
        let typeDisplay = '';
        let timeDisplay = '';
        
        switch (task.type) {
            case 'daily':
                typeDisplay = '<span class="badge bg-info">每日定时</span>';
                timeDisplay = task.time || '未设置';
                break;
            case 'weekly':
                typeDisplay = '<span class="badge bg-primary">每周定时</span>';
                const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
                const dayDisplay = (task.days || []).map(d => dayNames[d]).join(', ');
                timeDisplay = `${task.time || '未设置'} (${dayDisplay})`;
                break;
            case 'interval':
                typeDisplay = '<span class="badge bg-warning">间隔执行</span>';
                const unitMap = {
                    'seconds': '秒',
                    'minutes': '分钟',
                    'hours': '小时'
                };
                timeDisplay = `每 ${task.interval || 0} ${unitMap[task.unit] || '秒'}`;
                break;
            default:
                typeDisplay = '<span class="badge bg-secondary">未知类型</span>';
                timeDisplay = '未设置';
        }
        
        // 构建用户信息显示
        let userDisplay = '';
        if (task.user_type === 'phone') {
            if (task.user_ids && task.user_ids.length > 0) {
                // 显示用户数量
                userDisplay = `${task.user_ids.length} 个用户`;
                
                // 如果用户数量不多，则显示详细信息
                if (task.user_ids.length <= 3) {
                    userDisplay = task.user_ids.join(', ');
                }
            } else if (task.user_id) {
                // 兼容旧数据格式
                userDisplay = task.user_id;
            } else {
                userDisplay = '未设置';
            }
        } else { // index
            if (task.user_ids && task.user_ids.length > 0) {
                userDisplay = `索引 ${task.user_ids.join(', ')}`;
            } else if (task.user_id !== undefined) {
                userDisplay = `索引 ${task.user_id}`;
            } else {
                userDisplay = '未设置';
            }
        }
        
        // 构建最后执行结果显示
        let lastRunDisplay = '';
        if (task.last_run) {
            const statusDisplay = task.last_run.status ? 
                '<span class="badge bg-success">成功</span>' : 
                '<span class="badge bg-danger">失败</span>';
            
            lastRunDisplay = `
                <div>${task.last_run.time}</div>
                ${statusDisplay}
                <div class="small text-muted">${task.last_run.message || '无详情'}</div>
            `;
        } else {
            lastRunDisplay = '<span class="text-muted">从未执行</span>';
        }
        
        // 构建任务状态显示
        const statusDisplay = task.active !== false ? 
            '<span class="badge bg-success">激活</span>' : 
            '<span class="badge bg-secondary">禁用</span>';
        
        // 添加到表格
        const tr = $(`<tr data-id="${task.id}"></tr>`);
        tr.html(`
            <td>${task.id}</td>
            <td>${task.name || '未命名任务'}</td>
            <td>${typeDisplay}</td>
            <td>${timeDisplay}</td>
            <td>${userDisplay}</td>
            <td>${statusDisplay}</td>
            <td>${lastRunDisplay}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-info text-white edit-schedule" data-id="${task.id}" title="编辑任务">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-success execute-schedule" data-id="${task.id}" title="立即执行">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-danger delete-schedule" data-id="${task.id}" title="删除任务">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `);
        tbody.append(tr);
    });
}

// 执行定时任务
function executeSchedule(taskId) {
    if (!taskId) {
        showToast('任务ID无效', 'error');
        return;
    }
    
    // 显示确认对话框
    Swal.fire({
        title: '确认执行',
        text: '确定要立即执行此定时任务吗？',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: '确定执行',
        cancelButtonText: '取消',
        confirmButtonColor: '#28a745'
    }).then((result) => {
        if (result.isConfirmed) {
            // 显示加载中
            showLoading('正在执行任务...');
            
            // 发送请求执行任务
            axios.post(`/api/schedule/${taskId}/execute`)
                .then(function(response) {
                    hideLoading();
                    if (response.data.status) {
                        showToast('任务执行成功', 'success');
                        
                        // 显示详细结果
                        if (response.data.result && response.data.result.results) {
                            const results = response.data.result.results;
                            const totalCount = results.length;
                            const successCount = results.filter(r => r.status).length;
                            
                            let resultHTML = `
                                <div class="alert alert-success">
                                    <h5><i class="fas fa-check-circle me-2"></i>任务执行结果</h5>
                                    <p>总计 ${totalCount} 个用户，成功 ${successCount} 个，失败 ${totalCount - successCount} 个</p>
                                </div>
                                <div class="table-responsive">
                                    <table class="table table-sm table-striped">
                                        <thead>
                                            <tr>
                                                <th>用户ID</th>
                                                <th>状态</th>
                                                <th>消息</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                            `;
                            
                            results.forEach(result => {
                                const statusClass = result.status ? 'success' : 'danger';
                                const statusText = result.status ? '成功' : '失败';
                                
                                resultHTML += `
                                    <tr>
                                        <td>${result.user_id}</td>
                                        <td><span class="badge bg-${statusClass}">${statusText}</span></td>
                                        <td>${result.message || '无消息'}</td>
                                    </tr>
                                `;
                            });
                            
                            resultHTML += `
                                        </tbody>
                                    </table>
                                </div>
                            `;
                            
                            Swal.fire({
                                title: '执行结果',
                                html: resultHTML,
                                icon: 'info',
                                width: '800px'
                            });
                        }
                        
                        // 刷新任务列表
                        loadScheduleTasks();
                    } else {
                        showToast('任务执行失败: ' + response.data.message, 'error');
                    }
                })
                .catch(function(error) {
                    hideLoading();
                    console.error('执行任务失败:', error);
                    showToast('执行任务失败', 'error');
                });
        }
    });
}

// 删除定时任务
function deleteSchedule(taskId) {
    if (!taskId) {
        showToast('任务ID无效', 'error');
        return;
    }
    
    // 显示确认对话框
    Swal.fire({
        title: '确认删除',
        text: '确定要删除此定时任务吗？此操作无法恢复！',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        confirmButtonColor: '#dc3545'
    }).then((result) => {
        if (result.isConfirmed) {
            // 显示加载中
            showLoading('正在删除任务...');
            
            // 发送删除请求
            axios.delete(`/api/schedule/${taskId}`)
                .then(function(response) {
                    hideLoading();
                    if (response.data.status) {
                        showToast('任务删除成功', 'success');
                        loadScheduleTasks();  // 刷新任务列表
                    } else {
                        showToast('任务删除失败: ' + response.data.message, 'error');
                    }
                })
                .catch(function(error) {
                    hideLoading();
                    console.error('删除任务失败:', error);
                    showToast('删除任务失败', 'error');
                });
        }
    });
}

// 编辑定时任务
function editSchedule(taskId) {
    if (!taskId) {
        showToast('任务ID无效', 'error');
        return;
    }
    
    // 获取任务详情
    axios.get(`/api/schedule/${taskId}`)
        .then(function(response) {
            if (response.data.status && response.data.task) {
                const task = response.data.task;
                currentEditTaskId = task.id;
                
                // 填充表单
                $('#editScheduleId').val(task.id);
                $('#editScheduleName').val(task.name);
                $('#editScheduleType').val(task.type).trigger('change');
                
                if (task.type === 'daily' || task.type === 'weekly') {
                    $('#editScheduleTime').val(task.time);
                    $('#editTimeSettings').removeClass('d-none');
                    
                    if (task.type === 'weekly' && task.days) {
                        $('.editWeekday').prop('checked', false);
                        task.days.forEach(day => {
                            $(`#editWeekday${day}`).prop('checked', true);
                        });
                        $('#editWeekSettings').removeClass('d-none');
                    } else {
                        $('#editWeekSettings').addClass('d-none');
                    }
                } else {
                    $('#editTimeSettings').addClass('d-none');
                    $('#editWeekSettings').addClass('d-none');
                }
                
                if (task.type === 'interval') {
                    $('#editScheduleInterval').val(task.interval);
                    $('#editScheduleUnit').val(task.unit);
                    $('#editIntervalSettings').removeClass('d-none');
                } else {
                    $('#editIntervalSettings').addClass('d-none');
                }
                
                $('#editScheduleUserType').val(task.user_type).trigger('change');
                
                // 清除所有选中状态
                $('.edit-user-checkbox').prop('checked', false);
                
                if (task.user_type === 'phone') {
                    // 处理多个用户ID
                    const userIds = task.user_ids || (task.user_id ? [task.user_id] : []);
                    
                    // 标记选中的用户
                    userIds.forEach(userId => {
                        $(`#edit_user_${userId}`).prop('checked', true);
                    });
                    
                    // 更新全选框状态
                    updateSelectAllCheckbox('#editSelectAllUsers', '.edit-user-checkbox:not([disabled])');
                } else {
                    $('#editScheduleUserIndex').val(task.user_id);
                }
                
                // 处理位置参数
                if (task.location_address && task.location_lon && task.location_lat) {
                    // 有自定义位置参数
                    $('#editScheduleLocation').val('custom').trigger('change');
                    $('#editScheduleCustomAddress').val(task.location_address);
                    $('#editScheduleCustomLon').val(task.location_lon);
                    $('#editScheduleCustomLat').val(task.location_lat);
                } else if (task.location_preset_item !== undefined && task.location_preset_item !== null) {
                    // 使用预设位置
                    $('#editScheduleLocation').val(task.location_preset_item).trigger('change');
                } else {
                    // 使用默认位置
                    $('#editScheduleLocation').val('').trigger('change');
                }
                
                $('#editScheduleRandomOffset').prop('checked', task.location_random_offset !== false);
                $('#editScheduleActive').prop('checked', task.active !== false);
                
                $('#editScheduleModal').modal('show');
            } else {
                showToast('获取任务详情失败: ' + (response.data.message || '未知错误'), 'error');
            }
        })
        .catch(function(error) {
            console.error('获取任务详情失败:', error);
            showToast('获取任务详情失败', 'error');
        });
}

/**
 * 加载监控状态列表
 */
function loadMonitors() {
    showLoading('加载监控数据中...');
    
    axios.get('/api/monitors')
        .then(function(response) {
            if (response.data.status) {
                monitors = response.data.monitors || [];
                renderMonitorTable(monitors);
            } else {
                showToast('获取监控数据失败: ' + response.data.message, 'error');
                
                // 显示重试按钮
                Swal.fire({
                    title: '获取监控数据失败',
                    text: response.data.message || '服务器返回错误',
                    icon: 'error',
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    cancelButtonColor: '#d33',
                    confirmButtonText: '重试',
                    cancelButtonText: '关闭'
                }).then((result) => {
                    if (result.isConfirmed) {
                        loadMonitors(); // 重试加载
                    }
                });
            }
            hideLoading();
        })
        .catch(function(error) {
            console.error('获取监控数据失败:', error);
            hideLoading();
            
            let errorMessage = '网络错误，无法获取监控数据';
            if (error.response && error.response.data && error.response.data.message) {
                errorMessage = error.response.data.message;
            }
            
            // 显示错误并提供重试选项
            Swal.fire({
                title: '获取监控数据失败',
                text: errorMessage,
                icon: 'error',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: '重试',
                cancelButtonText: '关闭'
            }).then((result) => {
                if (result.isConfirmed) {
                    loadMonitors(); // 重试加载
                }
            });
        });
}

/**
 * 渲染监控状态表格
 */
function renderMonitorTable(monitors) {
    const tableBody = document.querySelector('#monitorTable tbody');
    tableBody.innerHTML = '';
    
    if (!monitors || monitors.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="9" class="text-center text-muted py-4">暂无监控数据</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // 遍历前先确保监控状态与is_running值一致
    monitors = monitors.map(monitor => {
        // 如果状态是stopped但is_running为true，修正为false
        if (monitor.status === 'stopped' && monitor.is_running === true) {
            console.log(`修正监控状态不一致: ${monitor.phone}`);
            return {...monitor, is_running: false};
        }
        return monitor;
    });
    
    monitors.forEach(function(monitor, index) {
        const row = document.createElement('tr');
        row.dataset.phone = monitor.phone;
        
        // 运行状态徽章
        let statusBadge = '';
        let statusClass = '';
        
        if (monitor.is_running) {
            statusBadge = '<span class="badge bg-success">运行中</span>';
            statusClass = 'table-success';
        } else if (monitor.status === 'stopped') {
            statusBadge = '<span class="badge bg-secondary">已停止</span>';
        } else {
            statusBadge = '<span class="badge bg-warning text-dark">未知</span>';
        }
        
        // 为运行中的监控行添加背景色
        if (statusClass) {
            row.classList.add(statusClass);
        }
        
        // 格式化时间，如果为空则显示"--"
        const formatTime = (timeStr) => timeStr ? timeStr : '--';
        
        // 创建操作按钮
        let actionButtons = '';
        if (monitor.is_running) {
            actionButtons = `
                <button class="btn btn-sm btn-danger stop-monitor" title="停止监控">
                    <i class="fas fa-stop"></i>
                </button>
            `;
        } else {
            actionButtons = `
                <button class="btn btn-sm btn-primary start-monitor" title="启动监控">
                    <i class="fas fa-play"></i>
                </button>
            `;
        }
        
        // 错误信息提示
        let errorInfo = '';
        if (monitor.last_error) {
            errorInfo = `<small class="d-block text-danger" title="${monitor.last_error}">
                <i class="fas fa-exclamation-circle"></i> ${monitor.last_error.length > 30 ? monitor.last_error.substring(0, 30) + '...' : monitor.last_error}
            </small>`;
        }
        
        const signCountBadge = monitor.sign_count > 0 ? 
            `<span class="badge bg-success">${monitor.sign_count}</span>` : 
            `<span class="badge bg-light text-dark">${monitor.sign_count || 0}</span>`;
            
        const errorCountBadge = monitor.error_count > 0 ? 
            `<span class="badge bg-danger">${monitor.error_count}</span>` : 
            `<span class="badge bg-light text-dark">${monitor.error_count || 0}</span>`;
        
        row.innerHTML = `
            <td>${monitor.phone}</td>
            <td>${monitor.username || '未知用户'}</td>
            <td>${statusBadge}</td>
            <td>${formatTime(monitor.start_time)}</td>
            <td>${formatTime(monitor.last_check_time)}</td>
            <td>${formatTime(monitor.last_sign_time)}</td>
            <td>${signCountBadge}</td>
            <td>${errorCountBadge} ${errorInfo}</td>
            <td>
                <div class="btn-group">
                    ${actionButtons}
                </div>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // 绑定监控操作事件
    document.querySelectorAll('#monitorTable .start-monitor').forEach(btn => {
        btn.addEventListener('click', function() {
            const phone = this.closest('tr').dataset.phone;
            showStartMonitorModal(phone);
        });
    });
    
    document.querySelectorAll('#monitorTable .stop-monitor').forEach(btn => {
        btn.addEventListener('click', function() {
            const phone = this.closest('tr').dataset.phone;
            stopMonitor(phone);
        });
    });
}

/**
 * 显示启动监控模态框
 */
function showStartMonitorModal(phone) {
    // 查找用户信息
    const user = users.find(u => u.phone === phone);
    if (!user) {
        showToast('未找到用户信息', 'error');
        return;
    }
    
    // 设置模态框用户信息
    document.getElementById('monitorPhone').value = phone;
    document.getElementById('monitorUsername').value = user.username || phone;
    document.getElementById('monitorDelay').value = '0'; // 默认延迟0秒
    
    // 加载位置预设
    const locationSelect = document.getElementById('monitorLocation');
    locationSelect.innerHTML = '<option value="">-- 使用默认位置 --</option>';
    
    // 显示位置预设信息
    if (userPresets[phone] && userPresets[phone].presets) {
        const presets = userPresets[phone].presets;
        if (presets.length === 0) {
            // 如果没有位置预设，添加提示信息
            const option = document.createElement('option');
            option.value = "";
            option.textContent = "未配置位置预设，将使用系统默认位置";
            option.disabled = true;
            locationSelect.appendChild(option);
        } else {
            // 添加每个位置预设
            presets.forEach((preset, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `预设 #${index+1}: ${preset.address} (${preset.lon}, ${preset.lat})`;
                locationSelect.appendChild(option);
            });
            
            // 选择第一个位置预设作为默认选项
            if (presets.length > 0) {
                locationSelect.value = "0";
            }
        }
    } else {
        // 如果未加载位置预设，添加提示信息
        const option = document.createElement('option');
        option.value = "";
        option.textContent = "未加载位置预设数据";
        option.disabled = true;
        locationSelect.appendChild(option);
    }
    
    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById('startMonitorModal'));
    modal.show();
}

/**
 * 启动监控
 */
function startMonitor() {
    const phone = document.getElementById('monitorPhone').value;
    const delay = parseInt(document.getElementById('monitorDelay').value) || 0;
    const locationPresetIndex = document.getElementById('monitorLocation').value;
    
    if (!phone) {
        showToast('无效的用户信息', 'error');
        return;
    }
    
    // 准备数据
    const data = {
        delay: delay
    };
    
    // 如果选择了位置预设，添加到请求
    if (locationPresetIndex !== '') {
        data.location_preset_index = parseInt(locationPresetIndex);
    }
    
    showLoading('启动监控中...');
    
    // 发送请求
    axios.post(`/api/monitors/${phone}/start`, data)
        .then(function(response) {
            if (response.data.status) {
                const detail = response.data.detail || {};
                const username = detail.username || '未知用户';
                const delayMsg = detail.delay > 0 ? `，签到延迟 ${detail.delay} 秒` : '';
                const locationMsg = detail.location_preset_index !== undefined ? 
                    `，使用位置预设 #${detail.location_preset_index + 1}` : '';
                
                showToast(`已成功启动 ${username} 的监控${delayMsg}${locationMsg}`, 'success');
                
                // 关闭模态框
                bootstrap.Modal.getInstance(document.getElementById('startMonitorModal')).hide();
                // 重新加载监控状态
                loadMonitors();
            } else {
                showToast('启动监控失败: ' + response.data.message, 'error');
            }
            hideLoading();
        })
        .catch(function(error) {
            console.error('启动监控失败:', error);
            let errorMessage = '启动监控失败';
            if (error.response && error.response.data && error.response.data.message) {
                errorMessage += ': ' + error.response.data.message;
            }
            showToast(errorMessage, 'error');
            hideLoading();
        });
}

/**
 * 停止监控
 */
function stopMonitor(phone) {
    if (!phone) {
        showToast('无效的用户信息', 'error');
        return;
    }
    
    // 确认对话框
    Swal.fire({
        title: '停止监控',
        text: '确定要停止此用户的监控吗？',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: '确定停止',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            showLoading('停止监控中...');
            
            // 发送请求
            axios.post(`/api/monitors/${phone}/stop`)
                .then(function(response) {
                    hideLoading();
                    
                    // 无论返回成功或失败，都启动检查序列，确保UI状态正确
                    checkMonitorStopStatus(phone, response.data.status);
                })
                .catch(function(error) {
                    console.error('停止监控失败:', error);
                    showToast('提交停止监控请求失败，将在后台继续尝试停止', 'error');
                    hideLoading();
                    
                    // 请求失败也启动检查序列
                    checkMonitorStopStatus(phone, false);
                });
        }
    });
}

/**
 * 检查监控停止状态
 * @param {string} phone - 用户手机号
 * @param {boolean} initialSuccess - 初始请求是否成功
 * @param {number} attempt - 当前尝试次数
 */
function checkMonitorStopStatus(phone, initialSuccess, attempt = 1) {
    const maxAttempts = 3; // 最大检查次数
    const initialDelay = 2000; // 初始延迟 (2秒)
    
    // 如果初始请求成功，显示成功消息，但仍然检查
    if (attempt === 1 && initialSuccess) {
        showToast('监控停止请求已发送', 'success');
    }
    
    // 计算当前检查的延迟时间 (逐次增加)
    const currentDelay = initialDelay * attempt;
    
    setTimeout(() => {
        // 检查监控状态
        axios.get('/api/monitors')
            .then(function(response) {
                if (response.data.status) {
                    const monitors = response.data.monitors || [];
                    const monitor = monitors.find(m => m.phone === phone);
                    
                    if (!monitor || !monitor.is_running) {
                        // 监控已停止
                        showToast('监控已成功停止', 'success');
                        // 刷新监控状态表格
                        renderMonitorTable(monitors);
                    } else if (attempt < maxAttempts) {
                        // 监控还在运行，继续检查
                        console.log(`监控停止检查 (${attempt}/${maxAttempts}): 监控仍在运行`);
                        checkMonitorStopStatus(phone, initialSuccess, attempt + 1);
                    } else {
                        // 达到最大检查次数，仍未停止
                        showToast('监控可能需要更长时间停止，请稍后刷新页面查看最新状态', 'warning');
                        // 强制刷新监控状态
                        loadMonitors();
                    }
                } else {
                    // API返回错误
                    if (attempt < maxAttempts) {
                        checkMonitorStopStatus(phone, initialSuccess, attempt + 1);
                    } else {
                        showToast('无法确认监控状态，请手动刷新页面', 'warning');
                        // 强制刷新监控状态
                        loadMonitors();
                    }
                }
            })
            .catch(function() {
                // 请求出错
                if (attempt < maxAttempts) {
                    checkMonitorStopStatus(phone, initialSuccess, attempt + 1);
                } else {
                    showToast('检查监控状态失败，请手动刷新页面', 'error');
                }
            });
    }, currentDelay);
}

/**
 * 停止所有监控
 */
function stopAllMonitors() {
    Swal.fire({
        title: '停止所有监控',
        text: '确定要停止所有正在运行的监控吗？',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: '确定停止全部',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            showLoading('停止所有监控中...');
            
            // 发送请求
            axios.post('/api/monitors/stop-all')
                .then(function(response) {
                    hideLoading();
                    
                    // 无论返回成功或失败，都启动检查序列
                    checkAllMonitorsStopStatus(response.data.status);
                })
                .catch(function(error) {
                    console.error('停止所有监控失败:', error);
                    showToast('提交停止监控请求失败，将在后台继续尝试停止', 'error');
                    hideLoading();
                    
                    // 请求失败也启动检查序列
                    checkAllMonitorsStopStatus(false);
                });
        }
    });
}

/**
 * 检查所有监控停止状态
 * @param {boolean} initialSuccess - 初始请求是否成功
 * @param {number} attempt - 当前尝试次数
 */
function checkAllMonitorsStopStatus(initialSuccess, attempt = 1) {
    const maxAttempts = 3; // 最大检查次数
    const initialDelay = 2000; // 初始延迟 (2秒)
    
    // 如果初始请求成功，显示成功消息，但仍然检查
    if (attempt === 1 && initialSuccess) {
        showToast('监控停止请求已发送', 'success');
    }
    
    // 计算当前检查的延迟时间 (逐次增加)
    const currentDelay = initialDelay * attempt;
    
    setTimeout(() => {
        // 检查监控状态
        axios.get('/api/monitors')
            .then(function(response) {
                if (response.data.status) {
                    const monitors = response.data.monitors || [];
                    const runningMonitors = monitors.filter(m => m.is_running);
                    
                    if (runningMonitors.length === 0) {
                        // 所有监控已停止
                        showToast('所有监控已成功停止', 'success');
                        // 刷新监控状态表格
                        renderMonitorTable(monitors);
                    } else if (attempt < maxAttempts) {
                        // 还有监控在运行，继续检查
                        console.log(`监控停止检查 (${attempt}/${maxAttempts}): 还有 ${runningMonitors.length} 个监控在运行`);
                        checkAllMonitorsStopStatus(initialSuccess, attempt + 1);
                    } else {
                        // 达到最大检查次数，仍有监控未停止
                        showToast(`尚有 ${runningMonitors.length} 个监控需要更长时间停止，请稍后刷新页面查看最新状态`, 'warning');
                        // 强制刷新监控状态
                        loadMonitors();
                    }
                } else {
                    // API返回错误
                    if (attempt < maxAttempts) {
                        checkAllMonitorsStopStatus(initialSuccess, attempt + 1);
                    } else {
                        showToast('无法确认监控状态，请手动刷新页面', 'warning');
                        // 强制刷新监控状态
                        loadMonitors();
                    }
                }
            })
            .catch(function() {
                // 请求出错
                if (attempt < maxAttempts) {
                    checkAllMonitorsStopStatus(initialSuccess, attempt + 1);
                } else {
                    showToast('检查监控状态失败，请手动刷新页面', 'error');
                }
            });
    }, currentDelay);
}