// 全局变量
let users = [];
let currentSelectedUser = null;
let userPresets = {};

// DOM元素加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    loadUsers();
    
    // 绑定事件
    document.getElementById('addUserBtn').addEventListener('click', addUser);
    document.getElementById('saveUserBtn').addEventListener('click', saveUser);
    document.getElementById('batchSignBtn').addEventListener('click', batchSign);
    document.getElementById('userSelect').addEventListener('change', userSelectChanged);
    document.getElementById('addLocationBtn').addEventListener('click', addLocationPreset);
    document.getElementById('batchSetLocationBtn').addEventListener('click', showBatchSetLocationModal);
    document.getElementById('saveBatchLocationBtn').addEventListener('click', saveBatchLocation);
    document.getElementById('togglePassword').addEventListener('click', togglePassword);
    
    // 设置导航链接功能
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        link.addEventListener('click', function() {
            document.querySelectorAll('.navbar-nav .nav-link').forEach(l => {
                l.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
});

// 加载用户列表
function loadUsers() {
    showLoading('用户列表');
    
    axios.get('/api/users')
        .then(response => {
            if (response.data.status) {
                users = response.data.users;
                updateUserTable();
                updateUserSelect();
                loadLocationPresets();
                hideLoading();
            } else {
                showError('加载用户失败: ' + response.data.message);
            }
        })
        .catch(error => {
            console.error('获取用户数据出错:', error);
            showError('获取用户数据时发生错误: ' + (error.message || '未知错误'));
        });
}

// 更新用户表格
function updateUserTable() {
    const tbody = document.querySelector('#userTable tbody');
    tbody.innerHTML = '';
    
    if (users.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="5" class="text-center">未找到用户，请添加新用户</td>';
        tbody.appendChild(tr);
        return;
    }
    
    users.forEach(user => {
        const tr = document.createElement('tr');
        
        // 激活状态样式
        const isActive = user.active !== false;
        if (!isActive) {
            tr.classList.add('table-secondary');
        }
        
        tr.innerHTML = `
            <td>${user.id !== undefined ? user.id : '-'}</td>
            <td>${user.username || '未知用户'}</td>
            <td>${user.phone || '-'}</td>
            <td><span class="badge ${isActive ? 'bg-success' : 'bg-secondary'}">${isActive ? '已激活' : '未激活'}</span></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-primary" onclick="editUser('${user.phone}')">编辑</button>
                    <button class="btn btn-success" onclick="signUser('${user.phone}')">签到</button>
                    <button class="btn btn-danger" onclick="deleteUser('${user.phone}')">删除</button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
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
    const addUserBtn = document.getElementById('addUserBtn');
    const originalText = addUserBtn.textContent;
    addUserBtn.textContent = '添加中...';
    addUserBtn.disabled = true;
    
    axios.post('/api/users', { phone, password })
        .then(response => {
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
            showError('添加用户时发生错误: ' + (error.message || '未知错误'));
        })
        .finally(() => {
            // 恢复按钮状态
            addUserBtn.textContent = originalText;
            addUserBtn.disabled = false;
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
    document.getElementById('editPhone').value = phone;
    document.getElementById('editUsername').value = user.username || '';
    document.getElementById('editPassword').value = '';
    document.getElementById('editActive').checked = user.active !== false;
    
    // 显示模态框
    new bootstrap.Modal(document.getElementById('editUserModal')).show();
}

// 保存编辑后的用户信息
function saveUser() {
    const phone = document.getElementById('editPhone').value;
    const username = document.getElementById('editUsername').value.trim();
    const password = document.getElementById('editPassword').value.trim();
    const active = document.getElementById('editActive').checked;
    
    // 构建要更新的数据
    const data = { username, active };
    if (password) {
        data.password = password;
    }
    
    // 显示加载状态
    const saveUserBtn = document.getElementById('saveUserBtn');
    const originalText = saveUserBtn.textContent;
    saveUserBtn.textContent = '保存中...';
    saveUserBtn.disabled = true;
    
    axios.put(`/api/users/${phone}`, data)
        .then(response => {
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
            showError('更新用户时发生错误: ' + (error.message || '未知错误'));
        })
        .finally(() => {
            // 恢复按钮状态
            saveUserBtn.textContent = originalText;
            saveUserBtn.disabled = false;
        });
}

// 删除用户
function deleteUser(phone) {
    if (!confirm(`确认要删除手机号为 ${phone} 的用户吗？`)) {
        return;
    }
    
    axios.delete(`/api/users/${phone}`)
        .then(response => {
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
            showError('删除用户时发生错误: ' + (error.message || '未知错误'));
        });
}

// 对单个用户进行签到
function signUser(phone) {
    if (!confirm(`确认要为手机号为 ${phone} 的用户执行签到吗？`)) {
        return;
    }
    
    // 获取签到设置
    const useRandomOffset = document.getElementById('useRandomOffset').checked;
    
    axios.post(`/api/sign/${phone}`, { location_random_offset: useRandomOffset })
        .then(response => {
            if (response.data.status) {
                showSuccess(`用户 ${phone} 签到成功`);
            } else {
                showError(`用户 ${phone} 签到失败: ${response.data.message}`);
            }
        })
        .catch(error => {
            console.error('签到出错:', error);
            showError('签到时发生错误: ' + (error.message || '未知错误'));
        });
}

// 批量签到
function batchSign() {
    if (!confirm('确认要为所有用户执行批量签到吗？')) {
        return;
    }
    
    // 获取签到设置
    const excludeInactive = document.getElementById('excludeInactiveUsers').checked;
    const useRandomOffset = document.getElementById('useRandomOffset').checked;
    
    // 显示加载状态
    const batchSignBtn = document.getElementById('batchSignBtn');
    const originalText = batchSignBtn.textContent;
    batchSignBtn.textContent = '签到中...';
    batchSignBtn.disabled = true;
    
    // 清空结果区域
    const resultDiv = document.getElementById('batchSignResult');
    resultDiv.innerHTML = '<div class="alert alert-info">正在执行批量签到，请稍候...</div>';
    
    // 签到请求
    axios.post('/api/sign/all', {
        exclude_inactive: excludeInactive,
        location_random_offset: useRandomOffset
    })
        .then(response => {
            if (response.data.status) {
                // 显示签到结果
                showBatchSignResults(response.data.results);
            } else {
                showError('批量签到失败: ' + response.data.message);
            }
        })
        .catch(error => {
            console.error('批量签到出错:', error);
            showError('批量签到时发生错误: ' + (error.message || '未知错误'));
        })
        .finally(() => {
            // 恢复按钮状态
            batchSignBtn.textContent = originalText;
            batchSignBtn.disabled = false;
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
    
    // 添加标题
    const header = document.createElement('h4');
    header.textContent = '签到结果';
    resultDiv.appendChild(header);
    
    // 计算签到统计
    const total = results.length;
    const success = results.filter(r => r.status).length;
    const failed = total - success;
    
    // 添加统计信息
    const stats = document.createElement('div');
    stats.className = 'alert alert-info mb-3';
    stats.innerHTML = `总计: ${total}个用户, 成功: ${success}个, 失败: ${failed}个`;
    resultDiv.appendChild(stats);
    
    // 添加详细结果
    results.forEach(result => {
        const item = document.createElement('div');
        item.className = 'result-item ' + (result.status ? 'result-success' : 'result-error');
        item.innerHTML = `
            <strong>${result.name} (${result.phone})</strong>: 
            ${result.status ? '成功' : '失败'} - ${result.message}
        `;
        resultDiv.appendChild(item);
    });
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
    const addLocationBtn = document.getElementById('addLocationBtn');
    const originalText = addLocationBtn.textContent;
    addLocationBtn.textContent = '添加中...';
    addLocationBtn.disabled = true;
    
    axios.post(`/api/location/presets/${phone}`, { address, lon, lat })
        .then(response => {
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
            showError('添加位置预设时发生错误: ' + (error.message || '未知错误'));
        })
        .finally(() => {
            // 恢复按钮状态
            addLocationBtn.textContent = originalText;
            addLocationBtn.disabled = false;
        });
}

// 删除位置预设
function deletePreset(phone, index) {
    if (!confirm('确认要删除这个位置预设吗？')) {
        return;
    }
    
    // TODO: 实现删除位置预设的API调用
    showError('删除位置预设功能暂未实现');
}

// 切换密码显示/隐藏
function togglePassword() {
    const passwordInput = document.getElementById('editPassword');
    const toggleBtn = document.getElementById('togglePassword');
    const icon = toggleBtn.querySelector('i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
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
    const saveBtn = document.getElementById('saveBatchLocationBtn');
    const originalText = saveBtn.textContent;
    saveBtn.textContent = '保存中...';
    saveBtn.disabled = true;
    
    // 批量设置位置
    const promises = selectedUsers.map(phone => 
        axios.post(`/api/location/presets/${phone}`, { address, lon, lat })
    );
    
    Promise.all(promises)
        .then(results => {
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
            showError('批量设置位置时发生错误: ' + (error.message || '未知错误'));
        })
        .finally(() => {
            // 恢复按钮状态
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        });
}

// 辅助函数：显示加载中
function showLoading(text = '加载中') {
    // 可以在这里实现加载效果，例如显示一个加载指示器
    console.log(`${text}...`);
}

// 辅助函数：隐藏加载中
function hideLoading() {
    // 隐藏加载指示器
}

// 辅助函数：显示成功消息
function showSuccess(message) {
    alert(message);
}

// 辅助函数：显示错误消息
function showError(message) {
    alert('错误: ' + message);
} 