// 全局变量
let users = [];
let currentSelectedUser = null;
let userPresets = {};
let monitorTasks = []; // 存储监听任务列表

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
    
    // 加载监听任务列表
    loadMonitorTasks();
    
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
    // 监听签到相关绑定
    $('#addMonitorBtn').on('click', addMonitorTask);
    $('#saveMonitorBtn').on('click', saveMonitorTask);
    
    // 批量选择用户相关绑定
    $('#showBatchUsersBtn').on('click', showBatchUsersSection);
    $('#closeBatchUsersBtn').on('click', hideBatchUsersSection);
    $('#selectAllUsers').on('change', toggleSelectAllUsers);
    
    // 监听模态框打开事件，确保每次打开时都重新加载用户列表
    $('#addMonitorModal').on('shown.bs.modal', function() {
        // 初始化批量选择状态
        hideBatchUsersSection();
        // 预先加载监听用户选项
        loadMonitorUserOptions();
    });

    // 设置导航链接功能
    $('.navbar-nav .nav-link').on('click', function() {
        $('.navbar-nav .nav-link').removeClass('active');
        $(this).addClass('active');
    });
    
    // 切换任务类型显示相应设置
    $('#scheduleType').change(function() {
        const type = $(this).val();
        
        // 隐藏所有设置面板
        $('#timeSettings').addClass('d-none');
        $('#weekSettings').addClass('d-none');
        $('#intervalSettings').addClass('d-none');
        $('#cookieUpdateSettings').addClass('d-none');
        $('#userSelectionContainer').removeClass('d-none');
        $('#userPhoneSelect').addClass('d-none');
        $('#userIndexInput').addClass('d-none');
        
        // 根据类型显示相应的设置面板
        if (type === 'daily' || type === 'weekly') {
            $('#timeSettings').removeClass('d-none');
            if (type === 'weekly') {
                $('#weekSettings').removeClass('d-none');
            }
            // 显示用户选择
            $('#userPhoneSelect').removeClass('d-none');
        } else if (type === 'interval') {
            $('#intervalSettings').removeClass('d-none');
            // 显示用户选择
            $('#userPhoneSelect').removeClass('d-none');
        } else if (type === 'cookie_update') {
            $('#cookieUpdateSettings').removeClass('d-none');
            // 隐藏通用用户选择
            $('#userSelectionContainer').addClass('d-none');
            $('#userPhoneSelect').addClass('d-none');
            $('#userIndexInput').addClass('d-none');
            // 加载用户列表到选择框
            loadUserOptionsForCookieUpdate();
        }
    });
    
    $('#editScheduleType').change(function() {
        const type = $(this).val();
        
        // 隐藏所有设置面板
        $('#editTimeSettings').addClass('d-none');
        $('#editWeekSettings').addClass('d-none');
        $('#editIntervalSettings').addClass('d-none');
        $('#editCookieUpdateSettings').addClass('d-none');
        $('#editUserSelectionContainer').removeClass('d-none');
        $('#editUserPhoneSelect').addClass('d-none');
        $('#editUserIndexInput').addClass('d-none');
        
        // 根据类型显示相应的设置面板
        if (type === 'daily' || type === 'weekly') {
            $('#editTimeSettings').removeClass('d-none');
            if (type === 'weekly' && task.days) {
                $('#editWeekSettings').removeClass('d-none');
            } else {
                $('#editWeekSettings').addClass('d-none');
            }
            
            // 显示用户选择
            $('#editUserPhoneSelect').removeClass('d-none');
        } else if (type === 'interval') {
            $('#editIntervalSettings').removeClass('d-none');
            // 显示用户选择
            $('#editUserPhoneSelect').removeClass('d-none');
        } else if (type === 'cookie_update') {
            $('#editCookieUpdateSettings').removeClass('d-none');
            // 隐藏通用用户选择
            $('#editUserSelectionContainer').addClass('d-none');
            $('#editUserPhoneSelect').addClass('d-none');
            $('#editUserIndexInput').addClass('d-none');
            // 加载用户列表到选择框
            loadUserOptionsForCookieUpdate(true);
        }
    });
    
    // 用户选择方式切换
    $('#scheduleUserType').change(function() {
        const userType = $(this).val();
        
        if (userType === 'phone') {
            $('#userPhoneSelect').removeClass('d-none');
            $('#userIndexInput').addClass('d-none');
        } else if (userType === 'index') {
            $('#userPhoneSelect').addClass('d-none');
            $('#userIndexInput').removeClass('d-none');
        } else if (userType === 'all') {
            $('#userPhoneSelect').addClass('d-none');
            $('#userIndexInput').addClass('d-none');
            showToast('全部用户模式将包含所有现有用户和之后新增的用户', 'info');
        }
    });
    
    // 编辑模态框中的用户选择方式切换
    $('#editScheduleUserType').change(function() {
        const userType = $(this).val();
        
        if (userType === 'phone') {
            $('#editUserPhoneSelect').removeClass('d-none');
            $('#editUserIndexInput').addClass('d-none');
        } else if (userType === 'index') {
            $('#editUserPhoneSelect').addClass('d-none');
            $('#editUserIndexInput').removeClass('d-none');
        } else if (userType === 'all') {
            $('#editUserPhoneSelect').addClass('d-none');
            $('#editUserIndexInput').addClass('d-none');
            showToast('全部用户模式将包含所有现有用户和之后新增的用户', 'info');
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
            active: $('#scheduleActive').is(':checked')
        };
        
        // 验证必填字段
        if (!formData.name || !formData.type) {
            showToast('请填写所有必填字段', 'error');
            return;
        }
        
        // 根据任务类型添加字段
        if (formData.type === 'daily' || formData.type === 'weekly') {
            formData.time = $('#scheduleTime').val();
            formData.user_type = $('#scheduleUserType').val();
            
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
            
            // 处理用户选择
            if (formData.user_type === 'phone') {
                const selectedUserIds = getSelectedUserIds('.user-checkbox');
                if (selectedUserIds.length === 0) {
                    showToast('请至少选择一个用户', 'error');
                    return;
                }
                formData.user_ids = selectedUserIds;
            } else if (formData.user_type === 'index') {
                const userIndex = $('#scheduleUserIndex').val();
                if (!userIndex && userIndex !== '0') {
                    showToast('请输入有效的用户索引', 'error');
                    return;
                }
                formData.user_ids = [userIndex];
            } else if (formData.user_type === 'all') {
                // 设置为全部用户
                formData.user_ids = ["all"];
            }
        } else if (formData.type === 'interval') {
            formData.interval = parseInt($('#scheduleInterval').val());
            formData.unit = $('#scheduleUnit').val();
            formData.user_type = $('#scheduleUserType').val();
            
            if (!formData.interval) {
                showToast('请输入有效的间隔值', 'error');
                return;
            }
            
            // 处理用户选择
            if (formData.user_type === 'phone') {
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
        } else if (formData.type === 'cookie_update') {
            formData.interval = parseInt($('#cookieUpdateInterval').val()) || 21;
            const userType = $('input[name="cookieUpdateUserType"]:checked').val();
            
            if (userType === 'all') {
                formData.user_type = 'all';
                formData.user_ids = [];  // 对于全部用户，不需要 user_ids
            } else {
                // 获取选中的用户
                const selectedUsers = [];
                $('.cookie-update-user-checkbox:checked').each(function() {
                    selectedUsers.push($(this).val());
                });
                
                if (selectedUsers.length === 0) {
                    showToast('请至少选择一个用户', 'error');
                    return;
                }
                
                formData.user_type = 'selected';
                formData.user_ids = selectedUsers;
            }
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
        const formData = {
            id: $('#editScheduleId').val(),
            name: $('#editScheduleName').val(),
            type: $('#editScheduleType').val(),
            active: $('#editScheduleActive').is(':checked'),
            location_random_offset: $('#editScheduleRandomOffset').is(':checked')
        };
        
        // 根据任务类型处理不同的参数
        if (formData.type === 'daily') {
            formData.time = $('#editScheduleTime').val();
            if (!formData.time) {
                showToast('请设置执行时间', 'error');
                return;
            }
            
            // 处理用户选择
            formData.user_type = $('#editScheduleUserType').val();
            if (formData.user_type === 'phone') {
                const selectedUserIds = getSelectedUserIds('.edit-user-checkbox');
                if (selectedUserIds.length === 0) {
                    showToast('请至少选择一个用户', 'error');
                    return;
                }
                formData.user_ids = selectedUserIds;
            } else if (formData.user_type === 'index') {
                const userIndex = $('#editScheduleUserIndex').val();
                if (!userIndex && userIndex !== '0') {
                    showToast('请输入有效的用户索引', 'error');
                    return;
                }
                formData.user_ids = [userIndex];
            } else if (formData.user_type === 'all') {
                // 设置为全部用户
                formData.user_ids = ["all"];
            }
        } else if (formData.type === 'weekly') {
            formData.time = $('#editScheduleTime').val();
            formData.days = [];
            $('.editWeekday:checked').each(function() {
                formData.days.push(parseInt($(this).val()));
            });
            if (!formData.time || formData.days.length === 0) {
                showToast('请设置执行时间和选择执行日期', 'error');
                return;
            }
            
            // 处理用户选择
            formData.user_type = $('#editScheduleUserType').val();
            if (formData.user_type === 'phone') {
                const selectedUserIds = getSelectedUserIds('.edit-user-checkbox');
                if (selectedUserIds.length === 0) {
                    showToast('请至少选择一个用户', 'error');
                    return;
                }
                formData.user_ids = selectedUserIds;
            } else if (formData.user_type === 'index') {
                const userIndex = $('#editScheduleUserIndex').val();
                if (!userIndex && userIndex !== '0') {
                    showToast('请输入有效的用户索引', 'error');
                    return;
                }
                formData.user_ids = [userIndex];
            } else if (formData.user_type === 'all') {
                // 设置为全部用户
                formData.user_ids = ["all"];
            }
        } else if (formData.type === 'interval') {
            formData.interval = parseInt($('#editScheduleInterval').val());
            formData.unit = $('#editScheduleUnit').val();
            
            if (!formData.interval || formData.interval < 1) {
                showToast('请设置有效的间隔时间', 'error');
                return;
            }
            
            // 处理用户选择
            formData.user_type = $('#editScheduleUserType').val();
            if (formData.user_type === 'phone') {
                const selectedUserIds = getSelectedUserIds('.edit-user-checkbox');
                if (selectedUserIds.length === 0) {
                    showToast('请至少选择一个用户', 'error');
                    return;
                }
                formData.user_ids = selectedUserIds;
            } else if (formData.user_type === 'index') {
                const userIndex = $('#editScheduleUserIndex').val();
                if (!userIndex && userIndex !== '0') {
                    showToast('请输入有效的用户索引', 'error');
                    return;
                }
                formData.user_ids = [userIndex];
            } else if (formData.user_type === 'all') {
                // 设置为全部用户
                formData.user_ids = ["all"];
            }
        } else if (formData.type === 'cookie_update') {
            formData.interval = parseInt($('#editCookieUpdateInterval').val());
            
            if (!formData.interval || formData.interval < 1) {
                showToast('请设置有效的更新间隔', 'error');
                return;
            }
            
            // 处理Cookie更新任务的用户选择
            const userType = $('input[name="editCookieUpdateUserType"]:checked').val();
            formData.user_type = userType;
            
            if (userType === 'selected') {
                const selectedUsers = [];
                $('.edit-cookie-update-user-checkbox:checked').each(function() {
                    selectedUsers.push($(this).val());
                });
                
                if (selectedUsers.length === 0) {
                    showToast('请至少选择一个用户', 'error');
                    return;
                }
                
                formData.user_ids = selectedUsers;
            } else if (userType === 'all') {
                formData.user_ids = [];  // 全部用户时不需要user_ids
            }
        }
        
        // 处理位置设置
        const locationPreset = $('#editScheduleLocation').val();
        if (locationPreset === 'custom') {
            formData.location = {
                address: $('#editScheduleCustomAddress').val(),
                lon: $('#editScheduleCustomLon').val(),
                lat: $('#editScheduleCustomLat').val()
            };
        } else if (locationPreset) {
            formData.location_preset_item = parseInt(locationPreset);
        }
        
        // 发送更新请求
        axios.put('/api/schedule/' + parseInt(formData.id), formData)
            .then(function(response) {
                if (response.data.status) {
                    showToast('任务更新成功', 'success');
                    $('#editScheduleModal').modal('hide');
                    loadScheduleTasks();
                } else {
                    showToast('更新失败: ' + response.data.message, 'error');
                }
            })
            .catch(function(error) {
                showToast('更新失败: ' + (error.response?.data?.message || error.message), 'error');
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
    console.log('开始加载用户数据...');
    showLoading('加载用户');
    
    axios.get('/api/users')
        .then(response => {
            console.log('用户数据接收成功:', response.data);
            hideLoading();
            
            if (response.data.status) {
                // 保存到全局变量
                users = response.data.users || [];
                console.log(`成功加载 ${users.length} 个用户`);
                
                // 更新表格和用户选择器
                updateUserTable();
                updateUserSelect();
                
                // 如果用户列表为空，提示添加用户
                if (users.length === 0) {
                    console.log('用户列表为空，显示提示');
                    $('#userTableBody').html(`
                        <tr>
                            <td colspan="6" class="text-center">
                                <div class="alert alert-info mb-0">
                                    <i class="fas fa-info-circle me-2"></i>还没有添加任何用户，请点击"添加用户"按钮开始添加
                                </div>
                            </td>
                        </tr>
                    `);
                }
            } else {
                console.error('加载用户数据失败:', response.data.message);
                showError(response.data.message || '加载用户列表失败');
                // 如果出错且没有用户数据，显示错误信息
                $('#userTableBody').html(`
                    <tr>
                        <td colspan="6" class="text-center">
                            <div class="alert alert-danger mb-0">
                                <i class="fas fa-exclamation-triangle me-2"></i>加载用户数据失败：${response.data.message || '未知错误'}
                            </div>
                        </td>
                    </tr>
                `);
            }
        })
        .catch(error => {
            console.error('加载用户列表请求出错:', error);
            hideLoading();
            
            let errorMsg = '加载用户列表时发生错误';
            if (error.response && error.response.data && error.response.data.message) {
                errorMsg += ': ' + error.response.data.message;
            } else if (error.message) {
                errorMsg += ': ' + error.message;
            } else {
                errorMsg += ': 未知错误';
            }
            
            showError(errorMsg);
            
            // 显示错误信息到表格
            $('#userTableBody').html(`
                <tr>
                    <td colspan="6" class="text-center">
                        <div class="alert alert-danger mb-0">
                            <i class="fas fa-exclamation-triangle me-2"></i>${errorMsg}
                        </div>
                    </td>
                </tr>
            `);
        });
}

// 更新用户表格
function updateUserTable() {
    const tableBody = $('#userTable tbody');
    tableBody.empty();

    
    // 如果没有用户，显示提示信息
    if (users.length === 0) {
        tableBody.html('<tr><td colspan="5" class="text-center">未找到用户，请添加新用户</td></tr>');
        return;
    }
    
    // 获取操作按钮和状态徽章模板
    const actionsTemplate = document.getElementById('userActionsTemplate').innerHTML;
    const statusTemplate = document.getElementById('userStatusTemplate').innerHTML;
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
        
        // 为状态徽章添加数据属性
        if (!user.phone || !/^1[3-9]\d{9}$/.test(user.phone)) {
            statusBadge.removeClass('clickable').addClass('disabled').attr('title', '手机号格式不正确');
        } else {
            statusBadge.attr('data-phone', user.phone).attr('data-active', user.active);
        }
        
        statusCell.append(statusBadge);
        row.append(statusCell);
        
        // 操作列 - 使用模板
        const actionCell = $('<td>');
        const actionButtons = $(actionTemplate.content.cloneNode(true));
        
        // 为按钮添加数据属性
        if (!user.phone || !/^1[3-9]\d{9}$/.test(user.phone)) {
            console.error(`用户 ${user.username || '未知'} 的手机号格式不正确: ${user.phone}`);
            // 对于手机号有问题的用户，禁用所有操作按钮
            actionButtons.find('.edit-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.toggle-active').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.delete-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.sign-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.monitor-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.toggle-monitor-user').addClass('disabled').attr('title', '手机号格式不正确');
        } else {
            actionButtons.find('.edit-user').attr('data-phone', user.phone);
            actionButtons.find('.toggle-active').attr('data-phone', user.phone).attr('data-active', user.active);
            actionButtons.find('.delete-user').attr('data-phone', user.phone);
            actionButtons.find('.sign-user').attr('data-phone', user.phone);
            actionButtons.find('.monitor-user').attr('data-phone', user.phone);
            actionButtons.find('.toggle-monitor-user').attr('data-phone', user.phone);
        }
        
        // 查找用户是否已有监听任务
        const hasMonitorTask = monitorTasks && monitorTasks.some(task => task.phone === user.phone);
        
        // 更新控制监听按钮状态
        if (hasMonitorTask) {
            actionButtons.find('.toggle-monitor-user')
                .removeClass('btn-secondary')
                .addClass('btn-success')
                .attr('title', '暂停监听')
                .attr('data-has-monitor', 'true');
        } else {
            actionButtons.find('.toggle-monitor-user')
                .removeClass('btn-success')
                .addClass('btn-secondary')
                .attr('title', '监听签到')
                .attr('data-has-monitor', 'false');
        }
        
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
        editUser(phone);
    });
    
    // 删除这个重复的事件绑定，因为在initUserManagement中已经使用事件委托方式绑定了
    // $('#userTable .toggle-active').click(function() {
    //     const phone = $(this).data('phone');
    //     const currentActive = $(this).data('active');
    //     toggleUserActive(phone, !currentActive);
    // });
    
    $('#userTable .delete-user').click(function() {
        const phone = $(this).data('phone');
        deleteUser(phone);
    });
    
    // 绑定状态徽章点击事件
    $('#userTable .status-badge.clickable').click(function() {
        const phone = $(this).data('phone');
        const currentActive = $(this).data('active');
        toggleUserActive(phone, !currentActive);
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
    
    console.log('正在发送添加用户请求...');
    axios.post('/api/users', { phone, password })
        .then(response => {
            console.log('收到添加用户响应:', response.data);
            hideLoading();
            if (response.data.status) {
                // 重置表单并关闭模态框
                document.getElementById('addUserForm').reset();
                bootstrap.Modal.getInstance(document.getElementById('addUserModal')).hide();
                
                // 等待一小段时间确保后端处理完成
                setTimeout(() => {
                    // 刷新用户列表
                    console.log('正在刷新用户列表...');
                    loadUsers();
                    
                    // 同时更新用户选项
                    loadUserOptions();
                    
                    showSuccess('用户添加成功');
                }, 500);
            } else {
                console.error('添加用户失败:', response.data.message);
                showError(response.data.message);
            }
        })
        .catch(error => {
            console.error('添加用户请求出错:', error);
            hideLoading();
            let errorMsg = '添加用户时发生错误';
            if (error.response && error.response.data && error.response.data.message) {
                errorMsg += ': ' + error.response.data.message;
            } else if (error.message) {
                errorMsg += ': ' + error.message;
            } else {
                errorMsg += ': 未知错误';
            }
            showError(errorMsg);
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
    return; // 添加return语句，确保函数在显示模态框后终止执行
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
    // 验证是否为手机号格式，如果不是，可能是错误传入了用户名
    if (!/^1[3-9]\d{9}$/.test(phone)) {
        showError(`请使用有效的手机号，"${phone}"看起来不是一个正确的手机号！`);
        return;
    }
    
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
    // 清空现有复选框
    const userCheckboxesContainer = $('#batchSetLocationModal .border');
    userCheckboxesContainer.empty();
    
    // 添加用户复选框
    users.forEach(user => {
        const checkbox = `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${user.phone}" id="userCheck_${user.phone}">
                <label class="form-check-label" for="userCheck_${user.phone}">
                    ${user.username || '未知用户'} (${user.phone})
                </label>
            </div>
        `;
        userCheckboxesContainer.append(checkbox);
    });
    
    // 使用jQuery打开模态窗口
    $('#batchSetLocationModal').modal('show');
}

// 保存批量位置设置
function saveBatchLocation() {
    const address = $('#batchLocationAddress').val().trim();
    const lon = $('#batchLocationLon').val().trim();
    const lat = $('#batchLocationLat').val().trim();
    
    if (!address || !lon || !lat) {
        showError('请填写完整的位置信息');
        return;
    }
    
    // 获取选中的用户
    const selectedUsers = $('#batchSetLocationModal input[type="checkbox"]:checked').map(function() {
        return $(this).val();
    }).get();
    
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
            $('#batchSetLocationModal').modal('hide');
            
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
                
                // 获取当前按钮和所在行
                const toggleButton = $(`.toggle-active[data-phone="${phone}"]`);
                const tr = toggleButton.closest('tr');
                
                // 更新表格行样式
                if (tr.length) {
                    if (isActive) {
                        tr.removeClass('table-secondary');
                    } else {
                        tr.addClass('table-secondary');
                    }
                }
                
                // 更新标签文本和样式
                const statusBadge = tr.find('.status-badge');
                if (statusBadge.length) {
                    statusBadge.text(isActive ? '已激活' : '未激活');
                    statusBadge.removeClass('active inactive').addClass(isActive ? 'active' : 'inactive');
                    statusBadge.attr('data-active', isActive);
                }
                
                // 更新按钮状态和样式
                toggleButton.attr('data-active', isActive);
                if (isActive) {
                    toggleButton.removeClass('btn-secondary').addClass('btn-warning');
                } else {
                    toggleButton.removeClass('btn-warning').addClass('btn-secondary');
                }
                
                // 刷新定时任务的用户列表
                loadUserOptions();
                
                // 刷新Cookie更新任务的用户列表
                loadUserOptionsForCookieUpdate();
                loadUserOptionsForCookieUpdate(true);
                
                showSuccess(`用户 ${phone} ${isActive ? '已激活' : '已停用'}`);
            } else {
                showError(response.data.message);
                // 不需要回滚UI状态，因为状态是根据按钮点击前的状态来确定的

            }
        })
        .catch(error => {
            console.error('更新用户状态出错:', error);
            showError('更新用户状态时发生错误: ' + (error.message || '未知错误'));
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
        
        // 为状态徽章添加数据属性
        if (!user.phone || !/^1[3-9]\d{9}$/.test(user.phone)) {
            statusBadge.removeClass('clickable').addClass('disabled').attr('title', '手机号格式不正确');
        } else {
            statusBadge.attr('data-phone', user.phone).attr('data-active', user.active);
        }
        
        statusCell.append(statusBadge);
        row.append(statusCell);
        
        // 操作列 - 使用模板
        const actionCell = $('<td>');
        const actionButtons = $(actionTemplate.content.cloneNode(true));
        
        // 为按钮添加数据属性
        if (!user.phone || !/^1[3-9]\d{9}$/.test(user.phone)) {
            console.error(`用户 ${user.username || '未知'} 的手机号格式不正确: ${user.phone}`);
            // 对于手机号有问题的用户，禁用所有操作按钮
            actionButtons.find('.edit-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.toggle-active').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.delete-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.sign-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.monitor-user').addClass('disabled').attr('title', '手机号格式不正确');
            actionButtons.find('.toggle-monitor-user').addClass('disabled').attr('title', '手机号格式不正确');
        } else {
            actionButtons.find('.edit-user').attr('data-phone', user.phone);
            actionButtons.find('.toggle-active').attr('data-phone', user.phone).attr('data-active', user.active);
            actionButtons.find('.delete-user').attr('data-phone', user.phone);
            actionButtons.find('.sign-user').attr('data-phone', user.phone);
            actionButtons.find('.monitor-user').attr('data-phone', user.phone);
            actionButtons.find('.toggle-monitor-user').attr('data-phone', user.phone);
        }
        
        // 查找用户是否已有监听任务
        const hasMonitorTask = monitorTasks && monitorTasks.some(task => task.phone === user.phone);
        
        // 更新控制监听按钮状态
        if (hasMonitorTask) {
            actionButtons.find('.toggle-monitor-user')
                .removeClass('btn-secondary')
                .addClass('btn-success')
                .attr('title', '暂停监听')
                .attr('data-has-monitor', 'true');
        } else {
            actionButtons.find('.toggle-monitor-user')
                .removeClass('btn-success')
                .addClass('btn-secondary')
                .attr('title', '监听签到')
                .attr('data-has-monitor', 'false');
        }
        
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
        editUser(phone);
    });
    
    // 删除这个重复的事件绑定，因为在initUserManagement中已经使用事件委托方式绑定了
    // $('#userTable .toggle-active').click(function() {
    //     const phone = $(this).data('phone');
    //     const currentActive = $(this).data('active');
    //     toggleUserActive(phone, !currentActive);
    // });
    
    $('#userTable .delete-user').click(function() {
        const phone = $(this).data('phone');
        deleteUser(phone);
    });
    
    // 绑定状态徽章点击事件
    $('#userTable .status-badge.clickable').click(function() {
        const phone = $(this).data('phone');
        const currentActive = $(this).data('active');
        toggleUserActive(phone, !currentActive);
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
                                id="user_${userPhone}">
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
                                id="edit_user_${userPhone}">
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
                    $('.user-checkbox').prop('checked', isChecked);
                });
                
                $('#editSelectAllUsers').on('change', function() {
                    const isChecked = $(this).prop('checked');
                    $('.edit-user-checkbox').prop('checked', isChecked);
                });
                
                // 当单个复选框更改时更新全选框状态
                $(document).on('change', '.user-checkbox', function() {
                    updateSelectAllCheckbox('#selectAllUsers', '.user-checkbox');
                });
                
                $(document).on('change', '.edit-user-checkbox', function() {
                    updateSelectAllCheckbox('#editSelectAllUsers', '.edit-user-checkbox');
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
            case 'cookie_update':
                typeDisplay = '<span class="badge bg-success">Cookie更新</span>';
                timeDisplay = `每 ${task.interval || 0} 天`;
                break;
            default:
                typeDisplay = '<span class="badge bg-secondary">未知类型</span>';
                timeDisplay = '未设置';
        }
        
        // 构建用户信息显示
        let userDisplay = '';
        if (task.type === 'cookie_update') {
            if (task.user_type === 'all') {
                userDisplay = '全部用户';
            } else if (task.user_type === 'selected' && task.user_ids && task.user_ids.length > 0) {
                userDisplay = `${task.user_ids.length} 个用户`;
                if (task.user_ids.length <= 3) {
                    userDisplay = task.user_ids.join(', ');
                }
            } else {
                userDisplay = '未设置';
            }
        } else {
            if (task.user_type === 'phone') {
                if (task.user_ids && task.user_ids.length > 0) {
                    userDisplay = `${task.user_ids.length} 个用户`;
                    if (task.user_ids.length <= 3) {
                        userDisplay = task.user_ids.join(', ');
                    }
                } else if (task.user_id) {
                    userDisplay = task.user_id;
                } else {
                    userDisplay = '未设置';
                }
            } else {
                if (task.user_ids && task.user_ids.length > 0) {
                    userDisplay = `索引 ${task.user_ids.join(', ')}`;
                } else if (task.user_id !== undefined) {
                    userDisplay = `索引 ${task.user_id}`;
                } else {
                    userDisplay = '未设置';
                }
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
        
        // 构建任务状态显示 - 使用滑动开关
        const isActive = task.active !== false;
        const statusDisplay = `
            <div class="form-check form-switch">
                <input class="form-check-input toggle-schedule" type="checkbox" 
                    data-id="${task.id}" ${isActive ? 'checked' : ''}>
                <label class="form-check-label">
                    ${isActive ? '<span class="badge bg-success">激活</span>' : '<span class="badge bg-secondary">禁用</span>'}
                </label>
            </div>
        `;
        
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
                    
                    // 设置用户选择方式
                    if (task.user_type) {
                        $('#editScheduleUserType').val(task.user_type).trigger('change');
                        
                        // 如果是按手机号选择
                        if (task.user_type === 'phone' && task.user_ids && task.user_ids.length > 0) {
                            // 选中已选择的用户
                            loadUserOptions(true);
                            setTimeout(() => {
                                task.user_ids.forEach(userId => {
                                    $(`#edituser_${userId}`).prop('checked', true);
                                });
                            }, 500);
                        } 
                        // 如果是按索引选择
                        else if (task.user_type === 'index' && task.user_ids && task.user_ids.length > 0) {
                            $('#editScheduleUserIndex').val(task.user_ids[0]);
                        }
                    }
                } else if (task.type === 'interval') {
                    $('#editScheduleInterval').val(task.interval);
                    $('#editScheduleUnit').val(task.unit);
                    $('#editIntervalSettings').removeClass('d-none');
                    
                    // 设置用户选择方式
                    if (task.user_type) {
                        $('#editScheduleUserType').val(task.user_type).trigger('change');
                        
                        // 如果是按手机号选择
                        if (task.user_type === 'phone' && task.user_ids && task.user_ids.length > 0) {
                            // 选中已选择的用户
                            loadUserOptions(true);
                            setTimeout(() => {
                                task.user_ids.forEach(userId => {
                                    $(`#edituser_${userId}`).prop('checked', true);
                                });
                            }, 500);
                        } 
                        // 如果是按索引选择
                        else if (task.user_type === 'index' && task.user_ids && task.user_ids.length > 0) {
                            $('#editScheduleUserIndex').val(task.user_ids[0]);
                        }
                    }
                } else if (task.type === 'cookie_update') {
                    $('#editCookieUpdateInterval').val(task.interval);
                    $('#editCookieUpdateSettings').removeClass('d-none');
                    
                    // 设置用户选择方式
                    if (task.user_type === 'all') {
                        $('#editCookieUpdateAllUsers').prop('checked', true);
                        $('#editCookieUpdateUserSelect').addClass('d-none');
                    } else {
                        $('#editCookieUpdateSelectedUsers').prop('checked', true);
                        $('#editCookieUpdateUserSelect').removeClass('d-none');
                        
                        // 加载用户列表到选择框
                        loadUserOptionsForCookieUpdate(true);
                        
                        // 选中已选择的用户
                        if (task.user_ids && task.user_ids.length > 0) {
                            task.user_ids.forEach(userId => {
                                $(`#edituser_${userId}`).prop('checked', true);
                            });
                        }
                    }
                }
                
                // 设置任务状态
                $('#editScheduleActive').prop('checked', task.active);
                
                // 显示编辑模态框
                $('#editScheduleModal').modal('show');
            } else {
                showToast('获取任务详情失败: ' + response.data.message, 'error');
            }
        })
        .catch(function(error) {
            console.error('获取任务详情失败:', error);
            showToast('获取任务详情失败', 'error');
        });
}

// 更新用户Cookie
function updateUserCookie(phone) {
    Swal.fire({
        title: '更新Cookie',
        text: `确认要更新用户 ${phone} 的Cookie吗？`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认更新',
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
            // 显示加载状态
            showLoading('更新Cookie中');
            
            axios.post(`/api/users/${phone}/update-cookie`)
                .then(response => {
                    hideLoading();
                    if (response.data.status) {
                        showSuccess(`用户 ${phone} Cookie更新成功`);
                    } else {
                        showError(`用户 ${phone} Cookie更新失败: ${response.data.message}`);
                    }
                })
                .catch(error => {
                    console.error('更新Cookie出错:', error);
                    hideLoading();
                    showError('更新Cookie时发生错误: ' + (error.message || '未知错误'));
                });
        }
    });
}

// 批量更新所有用户Cookie
function updateAllUserCookies() {
    Swal.fire({
        title: '批量更新Cookie',
        text: '确认要更新所有用户的Cookie吗？',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认更新',
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
            // 显示加载状态
            showLoading('批量更新Cookie中');
            
            axios.post('/api/users/update-all-cookies')
                .then(response => {
                    hideLoading();
                    if (response.data.status) {
                        showSuccess('所有用户Cookie更新成功');
                    } else {
                        showError('批量更新Cookie失败: ' + response.data.message);
                    }
                })
                .catch(error => {
                    console.error('批量更新Cookie出错:', error);
                    hideLoading();
                    showError('批量更新Cookie时发生错误: ' + (error.message || '未知错误'));
                });
        }
    });
}

// 初始化更新Cookie按钮事件
document.getElementById('updateCookieBtn').addEventListener('click', function() {
    Swal.fire({
        title: '选择更新方式',
        text: '请选择要更新的用户范围',
        showDenyButton: true,
        showCancelButton: true,
        confirmButtonText: '更新全部',
        denyButtonText: '选择用户',
        cancelButtonText: '取消',
        background: '#f8f9fa',
        customClass: {
            title: 'text-info',
            confirmButton: 'btn btn-success px-4',
            denyButton: 'btn btn-primary px-4',
            cancelButton: 'btn btn-secondary px-4',
            popup: 'swal-custom-popup'
        },
        showClass: {
            popup: 'swal2-show-custom'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            updateAllUserCookies();
        } else if (result.isDenied) {
            // 显示用户选择对话框
            const userOptions = users.map(user => ({
                text: `${user.username || '未知用户'} (${user.phone})`,
                value: user.phone
            }));
            
            Swal.fire({
                title: '选择用户',
                html: `
                    <div class="mb-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="selectAllUsersForCookie">
                            <label class="form-check-label" for="selectAllUsersForCookie">
                                全选
                            </label>
                        </div>
                        <hr>
                        <div class="user-checkboxes" style="max-height: 300px; overflow-y: auto;">
                            ${userOptions.map(option => `
                                <div class="form-check">
                                    <input class="form-check-input user-checkbox" type="checkbox" value="${option.value}" id="user-${option.value}">
                                    <label class="form-check-label" for="user-${option.value}">
                                        ${option.text}
                                    </label>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `,
                showCancelButton: true,
                confirmButtonText: '确认',
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
                },
                didOpen: () => {
                    // 全选功能
                    const selectAll = document.getElementById('selectAllUsersForCookie');
                    const checkboxes = document.querySelectorAll('.user-checkbox');
                    
                    selectAll.addEventListener('change', (e) => {
                        checkboxes.forEach(checkbox => {
                            checkbox.checked = e.target.checked;
                        });
                    });
                    
                    // 当所有复选框被选中时，自动选中全选框
                    checkboxes.forEach(checkbox => {
                        checkbox.addEventListener('change', () => {
                            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                            selectAll.checked = allChecked;
                        });
                    });
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    const selectedUsers = Array.from(document.querySelectorAll('.user-checkbox:checked')).map(cb => cb.value);
                    if (selectedUsers.length > 0) {
                        updateSelectedUserCookies(selectedUsers);
                    }
                }
            });
        }
    });
});

// 更新选中的用户Cookie
function updateSelectedUserCookies(phones) {
    Swal.fire({
        title: '更新Cookie',
        text: `确认要更新 ${phones.length} 个用户的Cookie吗？`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        cancelButtonColor: '#6c757d',
        confirmButtonText: '确认更新',
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
            // 显示加载状态
            showLoading('更新Cookie中');
            
            // 创建一个Promise数组，用于并行处理所有用户的Cookie更新
            const updatePromises = phones.map(phone => 
                axios.post(`/api/users/${phone}/update-cookie`)
                    .then(response => ({
                        phone,
                        success: response.data.status,
                        message: response.data.message
                    }))
                    .catch(error => ({
                        phone,
                        success: false,
                        message: error.response?.data?.message || '更新失败'
                    }))
            );
            
            // 等待所有更新完成
            Promise.all(updatePromises)
                .then(results => {
                    hideLoading();
                    
                    // 统计成功和失败的数量
                    const successCount = results.filter(r => r.success).length;
                    const failCount = results.filter(r => !r.success).length;
                    
                    // 显示结果
                    if (failCount === 0) {
                        showSuccess(`所有用户Cookie更新成功（共${phones.length}个）`);
                    } else {
                        // 显示详细结果
                        const failedUsers = results.filter(r => !r.success)
                            .map(r => `${r.phone}: ${r.message}`)
                            .join('\n');
                        
                        Swal.fire({
                            title: '部分用户更新失败',
                            html: `
                                <div class="text-start">
                                    <p>成功更新: ${successCount}个</p>
                                    <p>失败: ${failCount}个</p>
                                    <div class="mt-3">
                                        <h6>失败详情：</h6>
                                        <pre class="text-danger" style="white-space: pre-wrap;">${failedUsers}</pre>
                                    </div>
                                </div>
                            `,
                            icon: 'warning',
                            confirmButtonText: '确定'
                        });
                    }
                })
                .catch(error => {
                    console.error('批量更新Cookie出错:', error);
                    hideLoading();
                    showError('批量更新Cookie时发生错误: ' + (error.message || '未知错误'));
                });
        }
    });
}

// Cookie更新任务用户选择切换
$('input[name="cookieUpdateUserType"]').change(function() {
    if ($(this).val() === 'selected') {
        $('#cookieUpdateUserSelect').removeClass('d-none');
    } else {
        $('#cookieUpdateUserSelect').addClass('d-none');
    }
});

// Cookie更新任务全选/取消全选
$('#selectAllUsersForCookie').change(function() {
    $('.cookie-update-user-checkbox').prop('checked', $(this).prop('checked'));
});

// 加载用户选项到Cookie更新选择框
function loadUserOptionsForCookieUpdate(isEdit = false) {
    const prefix = isEdit ? 'edit' : '';
    const container = $(`#${prefix}CookieUpdateUserCheckboxes`);
    container.empty();
    
    // 获取用户列表
    axios.get('/api/users')
        .then(function(response) {
            if (response.data.status) {
                const users = response.data.users;
                
                // 生成用户选择框
                users.forEach(user => {
                    const isActive = user.active !== false;
                    const checkbox = $(`
                        <div class="form-check">
                            <input class="form-check-input ${prefix}cookie-update-user-checkbox" type="checkbox" value="${user.phone}" id="${prefix}user_${user.phone}">
                            <label class="form-check-label" for="${prefix}user_${user.phone}">
                                ${user.username || user.phone} ${isActive ? '' : '<span class="text-danger">[已禁用]</span>'}
                            </label>
                        </div>
                    `);
                    container.append(checkbox);
                });
            } else {
                showToast('获取用户列表失败: ' + response.data.message, 'error');
            }
        })
        .catch(function(error) {
            console.error('获取用户列表失败:', error);
            showToast('获取用户列表失败', 'error');
        });
}

// 编辑Cookie更新任务的用户选择方式切换
$('input[name="editCookieUpdateUserType"]').change(function() {
    if ($(this).val() === 'selected') {
        $('#editCookieUpdateUserSelect').removeClass('d-none');
        // 加载用户列表到选择框
        loadUserOptionsForCookieUpdate(true);
    } else {
        $('#editCookieUpdateUserSelect').addClass('d-none');
    }
});

// 编辑Cookie更新任务的全选/取消全选
$('#editSelectAllUsersForCookie').change(function() {
    $('.edit-cookie-update-user-checkbox').prop('checked', $(this).prop('checked'));
});

// 添加切换任务状态的处理函数
$(document).on('change', '.toggle-schedule', function() {
    const taskId = $(this).data('id');
    const isActive = $(this).is(':checked');
    
    // 显示加载中
    showLoading('正在更新任务状态...');
    
    // 发送请求切换状态
    axios.post(`/api/schedule/${taskId}/toggle`)
        .then(function(response) {
            hideLoading();
            if (response.data.status) {
                showToast('任务状态更新成功', 'success');
                loadScheduleTasks();  // 刷新任务列表
            } else {
                showToast('任务状态更新失败: ' + response.data.message, 'error');
                // 恢复开关状态
                $(this).prop('checked', !isActive);
            }
        })
        .catch(function(error) {
            hideLoading();
            console.error('更新任务状态失败:', error);
            showToast('更新任务状态失败', 'error');
            // 恢复开关状态
            $(this).prop('checked', !isActive);
        });
});

// 日志与统计功能
function loadLogs(limit = 100) {
    showLoading('加载日志中');
    const logType = document.getElementById('logTypeSelect').value;
    console.log('正在加载日志，类型:', logType, '限制行数:', limit);
    
    axios.get(`/api/logs?type=${logType}&limit=${limit}`)
        .then(response => {
            hideLoading();
            if (response.data.status) {
                const logs = response.data.logs;
                // 显示日志内容
                const logContent = document.getElementById('logContent');
                if (logs.length === 0) {
                    logContent.innerText = '暂无日志记录';
                } else {
                    logContent.innerText = logs.join('\n');
                    // 滚动到底部
                    const logContainer = logContent.parentElement;
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
            } else {
                showError('获取日志失败: ' + response.data.message);
            }
        })
        .catch(error => {
            hideLoading();
            console.error('获取日志出错:', error);
            showError('获取日志时发生错误: ' + (error.message || '未知错误'));
        });
}

function loadLogAnalysis() {
    showLoading('分析日志中');
    console.log('正在进行日志分析');
    
    axios.get('/api/logs/analyze')
        .then(response => {
            if (response.data.status) {
                const stats = response.data.stats;
                const activities = stats.recent_activities || [];
                
                // 更新活动表格
                updateActivitiesTable(activities);
            } else {
                showError('分析日志失败: ' + response.data.message);
            }
            hideLoading();
        })
        .catch(error => {
            hideLoading();
            console.error('分析日志出错:', error);
            showError('分析日志时发生错误: ' + (error.message || '未知错误'));
        });
}

function updateActivitiesTable(activities) {
    const table = document.getElementById('activitiesTable');
    
    if (!activities || activities.length === 0) {
        table.innerHTML = '<tr><td colspan="4" class="text-center">暂无活动记录</td></tr>';
        return;
    }
    
    let html = '';
    activities.forEach(activity => {
        const timestamp = activity.timestamp;
        let type = '';
        let status = '';
        let details = '';
        
        switch (activity.type) {
            case 'task_start':
                type = '<span class="badge bg-primary">任务开始</span>';
                status = '<span class="badge bg-secondary">-</span>';
                details = `任务名: ${activity.task_name} (ID: ${activity.task_id})`;
                break;
            case 'task_complete':
                type = '<span class="badge bg-info">任务完成</span>';
                if (activity.status === 'success') {
                    status = '<span class="badge bg-success">全部成功</span>';
                    details = `共 ${activity.users_count} 个用户`;
                } else if (activity.status === 'partial') {
                    status = '<span class="badge bg-warning">部分成功</span>';
                    details = `${activity.success_count}/${activity.total_count} 个用户成功`;
                } else if (activity.status === 'failed') {
                    status = '<span class="badge bg-danger">全部失败</span>';
                    details = `共 ${activity.users_count} 个用户`;
                }
                break;
            case 'user_sign':
                type = '<span class="badge bg-secondary">用户签到</span>';
                if (activity.status === 'success') {
                    status = '<span class="badge bg-success">成功</span>';
                } else {
                    status = '<span class="badge bg-danger">失败</span>';
                }
                details = `用户: ${activity.user_id}, 任务: ${activity.task_name}`;
                break;
            default:
                type = '<span class="badge bg-secondary">其他</span>';
                status = '<span class="badge bg-secondary">-</span>';
                details = activity.message || '-';
        }
        
        html += `
            <tr>
                <td>${timestamp}</td>
                <td>${type}</td>
                <td>${status}</td>
                <td>${details}</td>
            </tr>
        `;
    });
    
    table.innerHTML = html;
}

function loadSignStats() {
    showLoading('加载统计数据中');
    console.log('正在加载签到统计数据');
    
    axios.get('/api/stats/sign')
        .then(response => {
            hideLoading();
            if (response.data.status) {
                const stats = response.data.stats;
                
                // 更新用户统计
                document.getElementById('totalUsers').innerText = stats.total_users;
                document.getElementById('activeUsers').innerText = stats.active_users;
                document.getElementById('usersWithLocation').innerText = stats.users_with_location;
                document.getElementById('usersWithoutLocation').innerText = stats.users_without_location;
                
                // 更新任务统计
                document.getElementById('totalTasks').innerText = stats.total_tasks;
                document.getElementById('activeTasks').innerText = stats.active_tasks;
                
                // 更新最近签到统计
                const recentSigns = stats.recent_signs || { total: 0, success: 0, failed: 0 };
                document.getElementById('recentSuccess').innerText = recentSigns.success;
                document.getElementById('recentFailed').innerText = recentSigns.failed;
                
                // 更新成功率
                const successRate = stats.success_rate || 0;
                const successRateBar = document.getElementById('successRateBar');
                successRateBar.style.width = `${successRate}%`;
                successRateBar.innerText = `${successRate.toFixed(1)}%`;
                
                // 更新成功率详情
                document.getElementById('successRateDetails').innerText = 
                    `总计 ${recentSigns.total} 次签到，成功 ${recentSigns.success} 次，失败 ${recentSigns.failed} 次`;
            } else {
                showError('获取统计数据失败: ' + response.data.message);
            }
        })
        .catch(error => {
            hideLoading();
            console.error('获取统计数据出错:', error);
            showError('获取统计数据时发生错误: ' + (error.message || '未知错误'));
        });
}

// 初始化日志与统计功能
function initLogsAndStats() {
    console.log('初始化日志与统计功能');
    
    // 加载初始数据
    loadSignStats();
    loadLogAnalysis();
    loadLogs();
    
    // 绑定刷新按钮事件
    document.getElementById('refreshLogsBtn').addEventListener('click', function() {
        loadSignStats();
        loadLogAnalysis();
        loadLogs(parseInt(document.getElementById('logLimitSelect').value));
    });
    
    // 绑定日志刷新按钮事件
    document.getElementById('refreshLogsTableBtn').addEventListener('click', function() {
        loadLogs(parseInt(document.getElementById('logLimitSelect').value));
    });
    
    // 绑定日志行数选择事件
    document.getElementById('logLimitSelect').addEventListener('change', function() {
        loadLogs(parseInt(this.value));
    });
    
    // 绑定日志类型选择事件
    document.getElementById('logTypeSelect').addEventListener('change', function() {
        loadLogs(parseInt(document.getElementById('logLimitSelect').value));
    });
    
    // 绑定日志标签页切换事件
    document.getElementById('logs-tab').addEventListener('click', function() {
        loadLogs(parseInt(document.getElementById('logLimitSelect').value));
    });
    
    document.getElementById('activities-tab').addEventListener('click', function() {
        loadLogAnalysis();
    });
    
    document.getElementById('stats-tab').addEventListener('click', function() {
        loadSignStats();
    });
    
    console.log("日志和统计模块初始化完成");
}

// 各管理模块初始化

function initUserManagement() {
    // 绑定用户表格操作事件
    $('#userTable').on('click', '.edit-user', function() {
        const userRow = $(this).closest('tr');
        const phone = userRow.find('td:eq(2)').text();
        editUser(phone);
    });
    
    $('#userTable').on('click', '.delete-user', function() {
        const userRow = $(this).closest('tr');
        const phone = userRow.find('td:eq(2)').text();
        deleteUser(phone);
    });
    
    $('#userTable').on('click', '.sign-user', function() {
        const userRow = $(this).closest('tr');
        const phone = userRow.find('td:eq(2)').text();
        signUser(phone);
    });
    
    $('#userTable').on('click', '.toggle-active', function() {
        const userRow = $(this).closest('tr');
        const phone = userRow.find('td:eq(2)').text();
        // 修复：使用正确的类名判断状态 - active而非badge-success
        const isActive = userRow.find('.status-badge').hasClass('active');
        toggleUserActive(phone, !isActive);
    });
    
    $('#userTable').on('click', '.toggle-monitor-user', function() {
        const userRow = $(this).closest('tr');
        const phone = userRow.find('td:eq(2)').text();
        const hasMonitor = $(this).data('has-monitor') === 'true';
        toggleUserMonitor(phone, hasMonitor);
    });
    
    console.log("用户管理模块已初始化");
}

function initSignManagement() {
    // 签到管理页面的初始化
    $('#updateCookieBtn').click(function() {
        updateAllUserCookies();
    });
    
    console.log("签到管理模块已初始化");
}

function initMonitorManagement() {
    // 监听签到管理页面的初始化
    $('#monitorTable').on('click', '.edit-monitor', function() {
        const monitorRow = $(this).closest('tr');
        const monitorId = monitorRow.find('td:eq(0)').text();
        editMonitorTask(monitorId);
    });
    
    $('#monitorTable').on('click', '.delete-monitor', function() {
        const monitorRow = $(this).closest('tr');
        const monitorId = monitorRow.find('td:eq(0)').text();
        deleteMonitorTask(monitorId);
    });
    
    $('#monitorTable').on('click', '.toggle-monitor', function() {
        const monitorRow = $(this).closest('tr');
        const monitorId = monitorRow.find('td:eq(0)').text();
        const isActive = monitorRow.find('.status-badge').hasClass('badge-success');
        toggleMonitorActive(monitorId, !isActive);
    });
    
    console.log("监听签到管理模块已初始化");
}

function initScheduleManagement() {
    // 定时任务管理页面的初始化
    $('#scheduleTable').on('click', '.edit-schedule', function() {
        const scheduleRow = $(this).closest('tr');
        const taskId = scheduleRow.find('td:eq(0)').text();
        editSchedule(taskId);
    });
    
    $('#scheduleTable').on('click', '.delete-schedule', function() {
        const scheduleRow = $(this).closest('tr');
        const taskId = scheduleRow.find('td:eq(0)').text();
        deleteSchedule(taskId);
    });
    
    $('#scheduleTable').on('click', '.execute-schedule', function() {
        const scheduleRow = $(this).closest('tr');
        const taskId = scheduleRow.find('td:eq(0)').text();
        executeSchedule(taskId);
    });
    
    $('#scheduleTable').on('click', '.toggle-schedule', function() {
        const scheduleRow = $(this).closest('tr');
        const taskId = scheduleRow.find('td:eq(0)').text();
        const isActive = scheduleRow.find('.status-badge').hasClass('badge-success');
        toggleScheduleActive(taskId, !isActive);
    });
    
    $('#updateScheduleBtn').click(function() {
        updateSchedule();
    });
    
    $('#saveScheduleBtn').click(function() {
        addSchedule();
    });
    
    console.log("定时任务管理模块已初始化");
}

function initLocationManagement() {
    // 初始化位置管理功能
    $('#addLocationBtn').on('click', addLocationPreset);
    $('#batchSetLocationBtn').on('click', showBatchSetLocationModal);
    $('#saveBatchLocationBtn').on('click', saveBatchLocation);
    
    // 如果有用户选择器，绑定事件
    if(document.getElementById('userSelect')) {
        document.getElementById('userSelect').addEventListener('change', userSelectChanged);
    }
}

// 在页面加载完成后初始化所有功能
document.addEventListener('DOMContentLoaded', function() {
    console.log('页面加载完成，开始初始化功能');
    
    try {
        // 根据页面上的元素决定初始化哪些功能
        if (document.getElementById('userTable') || document.getElementById('addUserBtn')) {
            // 初始化用户管理
            initUserManagement();
        }
        
        if (document.getElementById('batchSignBtn')) {
            // 初始化签到功能
            initSignManagement();
        }
        
        if (document.getElementById('scheduleTable') || document.getElementById('addScheduleBtn')) {
            // 初始化任务管理
            initScheduleManagement();
        }
        
        if (document.getElementById('locationPresetsTable') || document.getElementById('batchSetLocationBtn')) {
            // 初始化位置管理
            initLocationManagement();
        }
        
        // 如果存在日志相关元素，初始化日志与统计功能
        if (document.getElementById('logs')) {
            initLogsAndStats();
        }
        
        console.log('所有页面功能初始化完成');
    } catch (error) {
        console.error('初始化功能时发生错误:', error);
    }
});

// 监听签到相关函数
function loadMonitorTasks() {
    showLoading('加载监听任务中...');
    
    axios.get('/api/monitor/list')
        .then(response => {
            hideLoading();
            if (response.data.code === 0) {
                monitorTasks = response.data.data || [];
                updateMonitorTable();
                
                // 初始化监听管理模块
                initMonitorManagement();
                
                // 加载用户选项到监听任务表单
                loadMonitorUserOptions();
                
                // 根据任务列表状态更新重置ID按钮的可见性
                updateResetIDButtonVisibility();
            } else {
                console.error('加载监听任务错误:', response.data.message);
                showToast('加载监听任务失败', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('加载监听任务错误:', error);
            showToast('加载监听任务出错', 'error');
        });
}

// 更新重置ID按钮的可见性
function updateResetIDButtonVisibility() {
    // 只有在没有任务时才显示重置ID按钮
    if (monitorTasks.length === 0) {
        // 如果按钮不存在则创建
        if ($('#resetMonitorIDBtn').length === 0) {
            const resetButton = $(`
                <button id="resetMonitorIDBtn" class="btn btn-outline-secondary ms-2">
                    <i class="fas fa-redo me-1"></i>重置ID计数器
                </button>
            `);
            
            // 添加点击事件
            resetButton.on('click', resetMonitorID);
            
            // 添加到按钮组
            $('.card-header .btn-warning').parent().append(resetButton);
        } else {
            $('#resetMonitorIDBtn').show();
        }
    } else {
        // 有任务时隐藏按钮
        $('#resetMonitorIDBtn').hide();
    }
}

// 重置监听任务ID计数器
function resetMonitorID() {
    Swal.fire({
        title: '确认重置ID?',
        text: '这将重置监听任务ID计数器，下一个创建的任务ID将从1开始',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: '确认重置',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            showLoading('重置ID计数器中...');
            
            axios.post('/api/monitor/reset-id')
                .then(response => {
                    hideLoading();
                    if (response.data.code === 0) {
                        showSuccess('监听任务ID已重置');
                    } else {
                        showError(response.data.message);
                    }
                })
                .catch(error => {
                    hideLoading();
                    showError('重置ID失败: ' + error.message);
                });
        }
    });
}

function updateMonitorTable() {
    $('#monitorTable tbody').empty();
    
    // 如果没有任务，显示提示信息
    if (monitorTasks.length === 0) {
        $('#monitorTable tbody').append(`
            <tr>
                <td colspan="7" class="text-center">暂无监听任务</td>
            </tr>
        `);
        return;
    }
    
    // 排序监听任务，活跃的排在前面
    const sortedTasks = [...monitorTasks].sort((a, b) => {
        // 首先按活跃状态排序
        if (a.active !== b.active) {
            return a.active ? -1 : 1;
        }
        // 然后按ID排序
        return a.id - b.id;
    });
    
    // 显示监听任务
    sortedTasks.forEach(task => {
        const isActive = task.active !== false;
        const statusClass = isActive ? 'success' : 'secondary';
        const statusText = isActive ? '运行中' : '已暂停';
        const toggleBtnClass = isActive ? 'danger' : 'success';
        const toggleBtnIcon = isActive ? 'pause' : 'play';
        const toggleBtnText = isActive ? '暂停' : '启用';
        
        // 格式化最后检查时间
        let lastCheckTime = '从未检查';
        if (task.last_check) {
            const checkDate = new Date(task.last_check);
            lastCheckTime = checkDate.toLocaleString('zh-CN');
        }
        
        // 获取课程信息显示
        let courseDisplay = '';
        if (task.monitor_all || !task.course_ids || task.course_ids.length === 0) {
            // 监听所有课程
            courseDisplay = '<span class="badge bg-info">所有课程</span>';
        } else {
            // 监听特定课程
            courseDisplay = `<span class="badge bg-primary">${task.course_ids.length}个课程</span>`;
        }
        
        // 生成操作按钮
        const actionsHtml = `
            <div class="btn-group">
                <button class="btn btn-sm btn-info text-white" onclick="editMonitorTask(${task.id})" title="编辑">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-${toggleBtnClass}" onclick="toggleMonitorActive(${task.id}, ${!isActive})" title="${toggleBtnText}">
                    <i class="fas fa-${toggleBtnIcon}"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteMonitorTask(${task.id})" title="删除">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>
        `;
        
        // 添加到表格
        $('#monitorTable tbody').append(`
            <tr>
                <td>${task.id}</td>
                <td>${getUserNameByPhone(task.phone)} (${task.phone})</td>
                <td>${courseDisplay}</td>
                <td><span class="badge bg-${statusClass}">${statusText}</span></td>
                <td>${task.interval}秒</td>
                <td>${lastCheckTime}</td>
                <td>${actionsHtml}</td>
            </tr>
        `);
    });
}

function addMonitorTask() {
    // 判断是单用户模式还是批量模式
    const isBatchMode = !$('#batchUsersSection').hasClass('d-none');
    let userPhones = [];
    
    if (isBatchMode) {
        // 获取选中的用户手机号
        $('.user-checkbox:checked').each(function() {
            userPhones.push($(this).val());
        });
        
        if (userPhones.length === 0) {
            showToast('请至少选择一个用户', 'error');
            return;
        }
    } else {
        // 单用户模式
        const phone = $('#monitorUser').val();
        if (!phone) {
            showToast('请选择用户', 'error');
            return;
        }
        userPhones.push(phone);
    }
    
    const courseIds = $('#courseIds').val();
    const interval = $('#monitorInterval').val();
    const minDelay = parseInt($('#minDelay').val()) || 0;
    const maxDelay = parseInt($('#maxDelay').val()) || 0;
    
    if (!interval) {
        showToast('请填写轮询间隔', 'error');
        return;
    }
    
    // 验证延迟时间
    if (minDelay < 0 || maxDelay < 0) {
        showToast('延迟时间不能为负数', 'error');
        return;
    }
    
    if (minDelay > maxDelay) {
        showToast('最小延迟时间不能大于最大延迟时间', 'error');
        return;
    }
    
    // 处理课程ID，转换为数组，空值表示监听所有课程
    let courseIdsArray = [];
    if (courseIds && courseIds.trim()) {
        courseIdsArray = courseIds.split(',').map(id => id.trim()).filter(id => id !== '');
    }
    
    // 设置延迟范围
    const delayRange = (minDelay > 0 || maxDelay > 0) ? [minDelay, maxDelay] : null;
    
    // 如果课程ID为空且是批量模式，直接开始创建任务
    if (courseIdsArray.length === 0 && isBatchMode) {
        createMonitorTasksForUsers(userPhones, [], parseInt(interval), delayRange);
        return;
    }
    
    // 如果课程ID为空，询问用户是否要监听所有课程
    if (courseIdsArray.length === 0) {
        Swal.fire({
            title: '监听所有课程?',
            text: '您没有指定课程ID，系统将自动监听该用户所有课程的签到活动',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: '确认监听所有课程',
            cancelButtonText: '取消'
        }).then((result) => {
            if (result.isConfirmed) {
                // 创建任务
                if (isBatchMode) {
                    createMonitorTasksForUsers(userPhones, [], parseInt(interval), delayRange);
                } else {
                    submitAddMonitorTask(userPhones[0], [], parseInt(interval), delayRange);
                }
            }
        });
    } else {
        // 直接添加指定课程的监听任务
        if (isBatchMode) {
            createMonitorTasksForUsers(userPhones, courseIdsArray, parseInt(interval), delayRange);
        } else {
            submitAddMonitorTask(userPhones[0], courseIdsArray, parseInt(interval), delayRange);
        }
    }
}

// 批量创建监听任务
function createMonitorTasksForUsers(phones, courseIdsArray, interval, delayRange) {
    showLoading(`正在为 ${phones.length} 个用户创建监听任务...`);
    
    // 记录创建结果
    const results = {
        success: 0,
        failed: 0,
        details: []
    };
    
    // 顺序创建任务
    const createNextTask = (index) => {
        if (index >= phones.length) {
            // 全部创建完成，显示结果
            hideLoading();
            
            if (results.failed === 0) {
                showSuccess(`成功为 ${results.success} 个用户创建监听任务`);
            } else {
                showToast(`创建完成: 成功 ${results.success} 个, 失败 ${results.failed} 个`, 
                          results.failed > 0 ? 'warning' : 'success');
            }
            
            $('#addMonitorModal').modal('hide');
            loadMonitorTasks();  // 重新加载任务列表
            return;
        }
        
        const phone = phones[index];
        
        // 创建单个任务
        axios.post('/api/monitor/add', {
            phone: phone,
            course_ids: courseIdsArray,
            interval: interval,
            delay_range: delayRange
        })
        .then(response => {
            if (response.data.code === 0) {
                results.success++;
                results.details.push({
                    phone: phone,
                    success: true,
                    message: '成功'
                });
            } else {
                results.failed++;
                results.details.push({
                    phone: phone,
                    success: false,
                    message: response.data.message
                });
            }
            
            // 处理下一个
            createNextTask(index + 1);
        })
        .catch(error => {
            results.failed++;
            results.details.push({
                phone: phone,
                success: false,
                message: error.message
            });
            
            // 处理下一个
            createNextTask(index + 1);
        });
    };
    
    // 开始创建第一个任务
    createNextTask(0);
}

// 实际提交添加监听任务的函数
function submitAddMonitorTask(phone, courseIdsArray, interval, delayRange) {
    showLoading('添加监听任务中...');
    
    axios.post('/api/monitor/add', {
        phone: phone,
        course_ids: courseIdsArray,
        interval: interval,
        delay_range: delayRange
    })
    .then(response => {
        hideLoading();
        if (response.data.code === 0) {
            $('#addMonitorModal').modal('hide');
            if (courseIdsArray.length === 0) {
                showSuccess('监听所有课程的任务添加成功');
            } else {
                showSuccess('监听任务添加成功');
            }
            loadMonitorTasks();  // 重新加载任务列表
        } else {
            showError('添加监听任务失败: ' + response.data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('添加监听任务错误:', error);
        showError('添加监听任务时发生错误: ' + error.message);
    });
}

function editMonitorTask(id) {
    const task = monitorTasks.find(t => t.id === parseInt(id));
    
    if (!task) {
        showError('未找到该监听任务');
        return;
    }
    
    // 填充表单
    $('#editMonitorId').val(task.id);
    $('#editMonitorUser').val(task.phone);
    $('#editCourseIds').val(task.course_ids.join(','));
    $('#editMonitorInterval').val(task.interval);
    $('#editMonitorActive').prop('checked', task.active);
    
    // 填充延迟范围
    const delayRange = task.delay_range || [0, 0];
    $('#editMinDelay').val(delayRange[0] || 0);
    $('#editMaxDelay').val(delayRange[1] || 0);
    
    // 打开编辑模态框
    $('#editMonitorModal').modal('show');
}

function saveMonitorTask() {
    const id = $('#editMonitorId').val();
    const phone = $('#editMonitorUser').val();
    const courseIds = $('#editCourseIds').val();
    const interval = $('#editMonitorInterval').val();
    const active = $('#editMonitorActive').is(':checked');
    const minDelay = parseInt($('#editMinDelay').val()) || 0;
    const maxDelay = parseInt($('#editMaxDelay').val()) || 0;
    
    if (!phone || !interval) {
        showToast('请填写必填字段：用户和轮询间隔', 'error');
        return;
    }
    
    // 验证延迟时间
    if (minDelay < 0 || maxDelay < 0) {
        showToast('延迟时间不能为负数', 'error');
        return;
    }
    
    if (minDelay > maxDelay) {
        showToast('最小延迟时间不能大于最大延迟时间', 'error');
        return;
    }
    
    // 处理课程ID，转换为数组，空值表示监听所有课程
    let courseIdsArray = [];
    if (courseIds && courseIds.trim()) {
        courseIdsArray = courseIds.split(',').map(id => id.trim()).filter(id => id !== '');
    }
    
    // 设置延迟范围
    const delayRange = (minDelay > 0 || maxDelay > 0) ? [minDelay, maxDelay] : null;
    
    // 如果课程ID为空，询问用户是否要监听所有课程
    if (courseIdsArray.length === 0) {
        Swal.fire({
            title: '监听所有课程?',
            text: '您没有指定课程ID，系统将自动监听该用户所有课程的签到活动',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: '确认监听所有课程',
            cancelButtonText: '取消'
        }).then((result) => {
            if (result.isConfirmed) {
                // 继续更新任务，使用空数组表示监听所有课程
                submitUpdateMonitorTask(id, phone, [], parseInt(interval), active, delayRange);
            }
        });
    } else {
        // 直接更新为指定课程的监听任务
        submitUpdateMonitorTask(id, phone, courseIdsArray, parseInt(interval), active, delayRange);
    }
}

// 实际提交更新监听任务的函数
function submitUpdateMonitorTask(id, phone, courseIdsArray, interval, active, delayRange) {
    showLoading('更新监听任务中...');
    
    axios.post('/api/monitor/update', {
        id: parseInt(id),
        phone: phone,
        course_ids: courseIdsArray,
        interval: interval,
        active: active,
        delay_range: delayRange
    })
    .then(response => {
        hideLoading();
        if (response.data.code === 0) {
            $('#editMonitorModal').modal('hide');
            if (courseIdsArray.length === 0) {
                showSuccess('监听所有课程的任务更新成功');
            } else {
                showSuccess('监听任务更新成功');
            }
            loadMonitorTasks();  // 重新加载任务列表
        } else {
            showError('更新监听任务失败: ' + response.data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('更新监听任务错误:', error);
        showError('更新监听任务时发生错误: ' + error.message);
    });
}

function deleteMonitorTask(id) {
    Swal.fire({
        title: '确认删除?',
        text: '删除后将停止监听该课程的签到，且无法恢复!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
    }).then((result) => {
        if (result.isConfirmed) {
            showLoading('删除监听任务中...');
            
            axios.post('/api/monitor/delete', { id: parseInt(id) })
                .then(response => {
                    hideLoading();
                    if (response.data.code === 0) {
                        showSuccess('监听任务已删除');
                        loadMonitorTasks();  // 重新加载任务列表
                    } else {
                        showError('删除监听任务失败: ' + response.data.message);
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('删除监听任务错误:', error);
                    showError('删除监听任务时发生错误: ' + error.message);
                });
        }
    });
}

function toggleMonitorActive(id, active) {
    showLoading(active ? '启用监听任务中...' : '暂停监听任务中...');
    
    axios.post('/api/monitor/toggle', {
        id: parseInt(id),
        active: active
    })
    .then(response => {
        hideLoading();
        if (response.data.code === 0) {
            showSuccess(active ? '监听任务已启用' : '监听任务已暂停');
            loadMonitorTasks();  // 重新加载任务列表
        } else {
            showError('更改监听任务状态失败: ' + response.data.message);
        }
    })
    .catch(error => {
        hideLoading();
        console.error('更改监听任务状态错误:', error);
        showError('更改监听任务状态时发生错误: ' + error.message);
    });
}

// 添加新函数用于加载监听用户选项
function loadMonitorUserOptions() {
    // 获取添加和编辑表单中的用户选择下拉列表元素
    const addUserSelect = $('#monitorUser');
    const editUserSelect = $('#editMonitorUser');
    
    // 清空现有选项（保留默认选项）
    addUserSelect.find('option:not(:first)').remove();
    editUserSelect.find('option:not(:first)').remove();
    
    // 遍历用户列表添加选项
    users.forEach(user => {
        const isActive = user.active !== false;
        // 只添加激活的用户
        if (isActive) {
            const optionText = `${user.username || '未知用户'} (${user.phone})`;
            const optionValue = user.phone;
            
            // 添加到添加表单
            addUserSelect.append(
                $('<option></option>').val(optionValue).text(optionText)
            );
            
            // 添加到编辑表单
            editUserSelect.append(
                $('<option></option>').val(optionValue).text(optionText)
            );
        }
    });
    
    console.log('监听签到用户选项已加载，共 ' + addUserSelect.find('option').length + ' 个选项');
}

// 根据手机号获取用户名的辅助函数
function getUserNameByPhone(phone) {
    const user = users.find(u => u.phone === phone);
    return user ? (user.username || '未知用户') : '未知用户';
}

// 显示批量选择用户区域
function showBatchUsersSection() {
    // 显示批量选择区域
    $('#batchUsersSection').removeClass('d-none');
    // 禁用单个用户选择
    $('#monitorUser').prop('disabled', true);
    
    // 加载用户列表到复选框列表
    loadUsersToCheckboxes();
}

// 隐藏批量选择用户区域
function hideBatchUsersSection() {
    // 隐藏批量选择区域
    $('#batchUsersSection').addClass('d-none');
    // 启用单个用户选择
    $('#monitorUser').prop('disabled', false);
}

// 全选/取消全选用户
function toggleSelectAllUsers() {
    console.log('Toggle all users 被触发');
    const checked = $('#selectAllUsers').is(':checked');
    console.log('全选状态:', checked);
    console.log('用户复选框数量:', $('.user-checkbox').length);
    
    // 确保所有复选框更新状态
    $('.user-checkbox').each(function() {
        $(this).prop('checked', checked);
    });
}

// 加载用户到复选框列表
function loadUsersToCheckboxes() {
    const container = $('.user-checkboxes-container');
    container.empty();
    
    // 过滤出激活的用户
    const activeUsers = users.filter(user => user.active !== false);
    
    if (activeUsers.length === 0) {
        container.append('<div class="alert alert-info">没有可用的用户</div>');
        return;
    }
    
    // 为每个用户创建复选框
    activeUsers.forEach(user => {
        const username = user.username || '未知用户';
        
        const checkboxItem = $(`
            <div class="form-check mb-1">
                <input class="form-check-input user-checkbox" type="checkbox" value="${user.phone}" id="user-${user.phone}">
                <label class="form-check-label" for="user-${user.phone}">
                    ${username} (${user.phone})
                </label>
            </div>
        `);
        
        container.append(checkboxItem);
    });
    
    // 确保复选框事件响应
    $('.user-checkbox').on('change', function() {
        // 如果有任何一个复选框未选中，取消"全选"复选框的选中状态
        if ($('.user-checkbox:not(:checked)').length > 0) {
            $('#selectAllUsers').prop('checked', false);
        } 
        // 如果所有复选框都选中，则选中"全选"复选框
        else if ($('.user-checkbox:checked').length === $('.user-checkbox').length) {
            $('#selectAllUsers').prop('checked', true);
        }
    });
    
    console.log('已加载用户复选框:', $('.user-checkbox').length);
}

// 为单个用户创建监听签到任务
function createMonitorForUser(phone) {
    // 获取用户信息
    const user = users.find(u => u.phone === phone);
    if (!user) {
        showToast('未找到用户信息', 'error');
        return;
    }
    
    // 创建简化版的监听签到弹窗
    Swal.fire({
        title: '创建监听签到',
        html: `
            <p>将为用户 <strong>${user.username || user.phone}</strong> 创建监听签到任务</p>
            <div class="mb-3">
                <label for="monitorInterval" class="form-label">轮询间隔（秒）</label>
                <input type="number" class="form-control" id="monitorInterval" value="60" min="10">
                <div class="form-text">建议设置为60秒或更长</div>
            </div>
            <div class="mb-3">
                <label class="form-label">课程设置</label>
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="courseOption" id="allCourses" value="all" checked>
                    <label class="form-check-label" for="allCourses">
                        监听所有课程
                    </label>
                </div>
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="courseOption" id="specificCourses" value="specific">
                    <label class="form-check-label" for="specificCourses">
                        指定课程ID（多个用英文逗号分隔）
                    </label>
                </div>
                <input type="text" class="form-control mt-2" id="courseIds" placeholder="例如: 12345,67890" disabled>
            </div>
            <div class="mb-3">
                <label class="form-label">延迟签到设置</label>
                <div class="form-check mb-2">
                    <input class="form-check-input" type="checkbox" id="enableDelayRange">
                    <label class="form-check-label" for="enableDelayRange">
                        启用随机延迟（秒）
                    </label>
                </div>
                <div class="input-group" id="delayRangeGroup" style="display: none;">
                    <input type="number" class="form-control" id="minDelay" placeholder="最小延迟" value="0" min="0">
                    <span class="input-group-text">~</span>
                    <input type="number" class="form-control" id="maxDelay" placeholder="最大延迟" value="30" min="0">
                </div>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: '创建',
        cancelButtonText: '取消',
        didOpen: () => {
            // 添加交互事件
            $('#specificCourses, #allCourses').on('change', function() {
                $('#courseIds').prop('disabled', $('#allCourses').prop('checked'));
            });
            
            $('#enableDelayRange').on('change', function() {
                $('#delayRangeGroup').toggle($(this).prop('checked'));
            });
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // 获取表单数据
            const interval = parseInt($('#monitorInterval').val());
            if (isNaN(interval) || interval < 10) {
                showToast('轮询间隔必须大于或等于10秒', 'error');
                return;
            }
            
            // 课程ID处理
            let courseIds = [];
            if ($('#specificCourses').prop('checked')) {
                const courseIdsText = $('#courseIds').val().trim();
                if (courseIdsText) {
                    // 分割并过滤掉空字符串
                    courseIds = courseIdsText.split(',')
                        .map(id => id.trim())
                        .filter(id => id !== '');
                }
            }
            
            // 延迟范围处理
            let delayRange = null;
            if ($('#enableDelayRange').prop('checked')) {
                const minDelay = parseInt($('#minDelay').val());
                const maxDelay = parseInt($('#maxDelay').val());
                
                if (isNaN(minDelay) || isNaN(maxDelay) || minDelay < 0 || maxDelay < 0) {
                    showToast('延迟时间必须是非负整数', 'error');
                    return;
                }
                
                if (minDelay > maxDelay) {
                    showToast('最小延迟不能大于最大延迟', 'error');
                    return;
                }
                
                delayRange = [minDelay, maxDelay];
            }
            
            // 创建监听任务
            submitAddMonitorTask(phone, courseIds, interval, delayRange);
        }
    });
}

// 控制用户监听签到功能
function toggleUserMonitor(phone, hasMonitor) {
    if (hasMonitor) {
        // 用户已有监听任务，找到对应的任务并关闭/删除
        const task = monitorTasks.find(t => t.phone === phone);
        if (task) {
            // 询问用户是要暂停还是删除
            Swal.fire({
                title: '控制监听任务',
                text: '您想要暂停还是删除该监听任务?',
                icon: 'question',
                showDenyButton: true,
                showCancelButton: true,
                confirmButtonText: '暂停任务',
                denyButtonText: '删除任务',
                cancelButtonText: '取消',
                confirmButtonColor: '#ffc107',
                denyButtonColor: '#dc3545'
            }).then((result) => {
                if (result.isConfirmed) {
                    // 暂停任务
                    toggleMonitorActive(task.id, false);
                } else if (result.isDenied) {
                    // 删除任务
                    deleteMonitorTask(task.id);
                }
            });
        } else {
            showToast('找不到该用户的监听任务', 'error');
            // 刷新任务列表
            loadMonitorTasks();
        }
    } else {
        // 用户没有监听任务，创建新任务
        createMonitorForUser(phone);
    }
}

// 添加定时任务
function addSchedule() {
    // 收集表单数据
    const formData = {
        name: $('#scheduleName').val(),
        type: $('#scheduleType').val(),
        active: $('#scheduleActive').is(':checked')
    };
    
    // 验证必填字段
    if (!formData.name || !formData.type) {
        showToast('请填写所有必填字段', 'error');
        return;
    }
    
    // 根据任务类型添加字段
    if (formData.type === 'daily' || formData.type === 'weekly') {
        formData.time = $('#scheduleTime').val();
        formData.user_type = $('#scheduleUserType').val();
        
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
        
        // 处理用户选择
        if (formData.user_type === 'phone') {
            const selectedUserIds = getSelectedUserIds('.user-checkbox');
            if (selectedUserIds.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            formData.user_ids = selectedUserIds;
        } else if (formData.user_type === 'index') {
            const userIndex = $('#scheduleUserIndex').val();
            if (!userIndex && userIndex !== '0') {
                showToast('请输入有效的用户索引', 'error');
                return;
            }
            formData.user_ids = [userIndex];
        } else if (formData.user_type === 'all') {
            // 设置为全部用户
            formData.user_ids = ["all"];
        }
    } else if (formData.type === 'interval') {
        formData.interval = parseInt($('#scheduleInterval').val());
        formData.unit = $('#scheduleUnit').val();
        formData.user_type = $('#scheduleUserType').val();
        
        if (!formData.interval) {
            showToast('请输入有效的间隔值', 'error');
            return;
        }
        
        // 处理用户选择
        if (formData.user_type === 'phone') {
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
    } else if (formData.type === 'cookie_update') {
        formData.interval = parseInt($('#cookieUpdateInterval').val()) || 21;
        const userType = $('input[name="cookieUpdateUserType"]:checked').val();
        
        if (userType === 'all') {
            formData.user_type = 'all';
            formData.user_ids = [];  // 对于全部用户，不需要 user_ids
        } else {
            // 获取选中的用户
            const selectedUsers = [];
            $('.cookie-update-user-checkbox:checked').each(function() {
                selectedUsers.push($(this).val());
            });
            
            if (selectedUsers.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            
            formData.user_type = 'selected';
            formData.user_ids = selectedUsers;
        }
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
}

// 更新定时任务
function updateSchedule() {
    const formData = {
        id: $('#editScheduleId').val(),
        name: $('#editScheduleName').val(),
        type: $('#editScheduleType').val(),
        active: $('#editScheduleActive').is(':checked'),
        location_random_offset: $('#editScheduleRandomOffset').is(':checked')
    };
    
    // 根据任务类型处理不同的参数
    if (formData.type === 'daily') {
        formData.time = $('#editScheduleTime').val();
        if (!formData.time) {
            showToast('请设置执行时间', 'error');
            return;
        }
        
        // 处理用户选择
        formData.user_type = $('#editScheduleUserType').val();
        if (formData.user_type === 'phone') {
            const selectedUserIds = getSelectedUserIds('.edit-user-checkbox');
            if (selectedUserIds.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            formData.user_ids = selectedUserIds;
        } else if (formData.user_type === 'index') {
            const userIndex = $('#editScheduleUserIndex').val();
            if (!userIndex && userIndex !== '0') {
                showToast('请输入有效的用户索引', 'error');
                return;
            }
            formData.user_ids = [userIndex];
        } else if (formData.user_type === 'all') {
            // 设置为全部用户
            formData.user_ids = ["all"];
        }
    } else if (formData.type === 'weekly') {
        formData.time = $('#editScheduleTime').val();
        formData.days = [];
        $('.edit-weekday:checked').each(function() {
            formData.days.push(parseInt($(this).val()));
        });
        
        if (!formData.time) {
            showToast('请设置执行时间', 'error');
            return;
        }
        
        if (formData.days.length === 0) {
            showToast('请选择至少一天', 'error');
            return;
        }
        
        // 处理用户选择
        formData.user_type = $('#editScheduleUserType').val();
        if (formData.user_type === 'phone') {
            const selectedUserIds = getSelectedUserIds('.edit-user-checkbox');
            if (selectedUserIds.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            formData.user_ids = selectedUserIds;
        } else if (formData.user_type === 'index') {
            const userIndex = $('#editScheduleUserIndex').val();
            if (!userIndex && userIndex !== '0') {
                showToast('请输入有效的用户索引', 'error');
                return;
            }
            formData.user_ids = [userIndex];
        } else if (formData.user_type === 'all') {
            // 设置为全部用户
            formData.user_ids = ["all"];
        }
    } else if (formData.type === 'interval') {
        formData.interval = parseInt($('#editScheduleInterval').val());
        formData.unit = $('#editScheduleUnit').val();
        
        if (!formData.interval) {
            showToast('请输入有效的间隔值', 'error');
            return;
        }
        
        // 处理用户选择
        formData.user_type = $('#editScheduleUserType').val();
        if (formData.user_type === 'phone') {
            const selectedUserIds = getSelectedUserIds('.edit-user-checkbox');
            if (selectedUserIds.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            formData.user_ids = selectedUserIds;
        } else if (formData.user_type === 'index') {
            const userIndex = $('#editScheduleUserIndex').val();
            if (!userIndex && userIndex !== '0') {
                showToast('请输入有效的用户索引', 'error');
                return;
            }
            formData.user_ids = [userIndex];
        }
    } else if (formData.type === 'cookie_update') {
        formData.interval = parseInt($('#editCookieUpdateInterval').val()) || 21;
        
        // 获取更新用户类型
        const userType = $('input[name="editCookieUpdateUserType"]:checked').val();
        
        if (userType === 'all') {
            formData.user_type = 'all';
            formData.user_ids = []; // 对于全部用户，不需要 user_ids
        } else {
            // 获取选中的用户
            const selectedUsers = [];
            $('.edit-cookie-update-user-checkbox:checked').each(function() {
                selectedUsers.push($(this).val());
            });
            
            if (selectedUsers.length === 0) {
                showToast('请至少选择一个用户', 'error');
                return;
            }
            
            formData.user_type = 'selected';
            formData.user_ids = selectedUsers;
        }
    }
    
    // 处理位置参数
    const locationPreset = $('#editScheduleLocation').val();
    
    if (locationPreset === 'custom') {
        formData.location_address = $('#editScheduleCustomAddress').val();
        formData.location_lon = $('#editScheduleCustomLon').val();
        formData.location_lat = $('#editScheduleCustomLat').val();
        
        if (!formData.location_address || !formData.location_lon || !formData.location_lat) {
            showToast('请填写完整的自定义位置信息', 'error');
            return;
        }
    } else if (locationPreset) {
        formData.location_preset_item = locationPreset;
    }
    
    // 发送请求
    axios.put('/api/schedule/' + parseInt(formData.id), formData)
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