// HTML DOM 元素
const employeeList = document.getElementById('employeeList');
const addEmployeeBtn = document.getElementById('addEmployeeBtn');
const addEmployeeModal = document.getElementById('addEmployeeModal');
const addEmployeeForm = document.getElementById('addEmployeeForm');
const cancelAddEmployeeBtn = document.getElementById('cancelAddEmployee');
const editModal = document.getElementById('editModal');
const editForm = document.getElementById('editForm');
const editNameInput = document.getElementById('editNameInput');
const editJobTitleInput = document.getElementById('editJobTitleInput');
const editDepartmentInput = document.getElementById('editDepartmentInput');
const editLocationInput = document.getElementById('editLocationInput');
const editPhoneInput = document.getElementById('editPhoneInput');
const editEmergencyContactInput = document.getElementById('editEmergencyContactInput');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const currentPageSpan = document.getElementById('currentPage');

// 員工資料
let employees = [];
const itemsPerPage = 10;
let currentPage = 1;
let startIndex = 0;
let endIndex = itemsPerPage;

// 初始化
function initialize() {
  addEmployeeBtn.addEventListener('click', showAddEmployeeModal);
  cancelAddEmployeeBtn.addEventListener('click', hideAddEmployeeModal);
  editForm.addEventListener('submit', editEmployee);
  prevPageBtn.addEventListener('click', prevPage);
  nextPageBtn.addEventListener('click', nextPage);
  editModal.addEventListener('click', e => {
    if (e.target === editModal) {
      editModal();
    }
  });
  addEmployeeForm.addEventListener('submit', addEmployee);
  renderEmployeeList();
}
initialize();

// 顯示新增員工弹出窗口
function showAddEmployeeModal() {
  addEmployeeModal.style.display = 'block';
}

// 隱藏新增員工弹出窗口
function hideAddEmployeeModal() {
  addEmployeeModal.style.display = 'none';
  addEmployeeForm.reset();
}

// 新增員工
function addEmployee(event) {
  event.preventDefault();
  const name = addEmployeeForm.elements.name.value;
  const jobTitle = addEmployeeForm.elements.jobTitle.value;
  const department = addEmployeeForm.elements.department.value;
  const location = addEmployeeForm.elements.location.value;
  const phone = addEmployeeForm.elements.phone.value;
  const emergencyContact = addEmployeeForm.elements.emergencyContact.value;
  const personalFiles = addEmployeeForm.elements.personalFiles.files;
  const newEmployee = {
    id: employees.length + 1,
    name,
    jobTitle,
    department,
    location,
    phone,
    emergencyContact,
    personalFiles,
  };
  employees.push(newEmployee);
  currentPage = 1;
  startIndex = 0;
  endIndex = itemsPerPage;
  renderEmployeeList();
  hideAddEmployeeModal();
}

// 顯示編輯員工弹出窗口
function showEditModal(employee) {
  editNameInput.value = employee.name;
  editJobTitleInput.value = employee.jobTitle;
  editDepartmentInput.value = employee.department;
  editLocationInput.value = employee.location;
  editPhoneInput.value = employee.phone;
  editEmergencyContactInput.value = employee.emergencyContact;
  editForm.elements.employeeId.value = employee.id;
  editModal.style.display = 'block';
}

document.addEventListener('DOMContentLoaded', function() {
  // 获取关闭按钮元素
  // var closeButton = document.querySelector('.close');
  var closeButton = document.getElementById('closeBtn');

  // 添加点击事件监听器
  closeButton.addEventListener('click', function() {
    // 获取模态框元素
    var modal = document.getElementById('addEmployeeModal');

    // 隐藏模态框
    modal.style.display = 'none';

    // 可以在这里执行其他操作，或者不执行任何操作
  });
});




// 編輯員工
function editEmployee(event) {
  event.preventDefault();
  const employeeId = editForm.elements.employeeId.value;
  const employee = employees.find(e => e.id === Number(employeeId));
  if (employee) {
    employee.name = editForm.elements.name.value;
    employee.jobTitle = editForm.elements.jobTitle.value;
    employee.department = editForm.elements.department.value;
    employee.location = editForm.elements.location.value;
    employee.phone = editForm.elements.phone.value;
    employee.emergencyContact = editForm.elements.emergencyContact.value;
  }
  hideEditModal();
  renderEmployeeList();
}

// 渲染員工列表
function renderEmployeeList() {
  employeeList.innerHTML = '';
  const paginatedEmployees = employees.slice(startIndex, endIndex);
  paginatedEmployees.forEach(employee => {
    const row = document.createElement('tr');
    const columns = ['id', 'name', 'jobTitle', 'department', 'location', 'phone', 'emergencyContact']
      .map(key => {
        const cell = document.createElement('td');
        cell.textContent = employee[key];
        return cell;
      });
    row.append(...columns);
    employeeList.appendChild(row);
  });

  currentPageSpan.textContent = currentPage;
  prevPageBtn.disabled = currentPage === 1;
  nextPageBtn.disabled = endIndex >= employees.length;
}

// 上一頁
function prevPage() {
  if (startIndex > 0) {
    currentPage--;
    startIndex -= itemsPerPage;
    endIndex -= itemsPerPage;
    renderEmployeeList();
  }
}

// 下一頁
function nextPage() {
  if (endIndex < employees.length) {
    currentPage++;
    startIndex += itemsPerPage;
    endIndex += itemsPerPage;
    renderEmployeeList();
  }
}


// 搜索员工
// const searchInput = document.getElementById('searchInput');
// const searchBtn = document.getElementById('searchBtn');
// const employeeList = document.getElementById('employeeList');
// const rows = employeeList.getElementsByTagName('tr');

// searchInput.addEventListener('input', filterEmployees);
// searchBtn.addEventListener('click', filterEmployees);

// function filterEmployees() {
//   const searchTerm = searchInput.value.toLowerCase();
//   for (let i = 0; i < rows.length; i++) {
//     const cells = rows[i].getElementsByTagName('td');
//     let match = false;
//     for (let j = 0; j < cells.length; j++) {
//       if (cells[j].innerText.toLowerCase().includes(searchTerm)) {
//         match = true;
//         break;
//       }
//     }
//     if (match) {
//       rows[i].style.display = '';
//     } else {
//       rows[i].style.display = 'none';
//     }
//   }
// }

// // 新增员工
// const addEmployeeBtn = document.getElementById('addEmployeeBtn');
// const addEmployeeModal = document.getElementById('addEmployeeModal');
// const closeBtn = document.querySelectorAll('.close');
// const cancelAddEmployeeBtn = document.getElementById('cancelAddEmployee');
// const addEmployeeForm = document.getElementById('addEmployeeForm');
// addEmployeeBtn.addEventListener('click', () => {
//   addEmployeeModal.style.display = 'block';
// });
// closeBtn.forEach(btn => {
//   btn.addEventListener('click', () => {
//     addEmployeeModal.style.display = 'none';
//     editModal.style.display = 'none';
//   });
// });
// cancelAddEmployeeBtn.addEventListener('click', () => {
//   addEmployeeModal.style.display = 'none';
// });
// addEmployeeForm.addEventListener('submit', async (event) => {
//   event.preventDefault();
//   const formData = new FormData(addEmployeeForm);
//   try {
//     const response = await fetch('/add_employee', {
//       method: 'POST',
//       body: formData
//     });
//     if (response.ok) {
//       addEmployeeModal.style.display = 'none';
//       location.reload(); // 重新加载页面以显示新员工
//     } else {
//       console.error('Error adding employee');
//     }
//   } catch (error) {
//     console.error('Error:', error);
//   }
// });
// // 编辑员工
// const editModal = document.getElementById('editModal');
// const editForm = document.getElementById('editForm');
// const cancelEditEmployeeBtn = document.getElementById('cancelEditEmployee');
// const editBtns = document.querySelectorAll('.edit-btn');
// editBtns.forEach(btn => {
//   btn.addEventListener('click', () => {
//     const employeeId = btn.dataset.employeeId;
//     // 从服务器获取员工数据并填充编辑表单
//     fetch(`/get_employee/${employeeId}`, {
//       method: 'GET'
//     })
//       .then(response => response.json())
//       .then(employee => {
//         editModal.style.display = 'block';
//         const form = editForm;
//         form.elements.employeeId.value = employee.employee_id;
//         form.elements.name.value = employee.name;
//         form.elements.jobTitle.value = employee.job_title;
//         form.elements.department.value = employee.department;
//         form.elements.location.value = employee.location;
//         form.elements.phone.value = employee.phone;
//         form.elements.emergencyContact.value = employee.emergency_contact;
//       })
//       .catch(error => console.error('Error:', error));
//   });
// });
// cancelEditEmployeeBtn.addEventListener('click', () => {
//   editModal.style.display = 'none';
// });
// editForm.addEventListener('submit', async (event) => {
//   event.preventDefault();
//   const formData = new FormData(editForm);
//   try {
//     const response = await fetch('/update_employee', {
//       method: 'POST',
//       body: formData
//     });
//     if (response.ok) {
//       editModal.style.display = 'none';
//       location.reload(); // 重新加载页面以显示更新后的员工数据
//     } else {
//       console.error('Error updating employee');
//     }
//   } catch (error) {
//     console.error('Error:', error);
//   }
// });
// // 删除员工
// const deleteBtns = document.querySelectorAll('.delete-btn');
// deleteBtns.forEach(btn => {
//   btn.addEventListener('click', async () => {
//     const employeeId = btn.dataset.employeeId;
//     try {
//       const response = await fetch(`/delete_employee/${employeeId}`, {
//         method: 'DELETE'
//       });
//       if (response.ok) {
//         location.reload(); // 重新加载页面以刷新员工列表
//       } else {
//         console.error('Error deleting employee');
//       }
//     } catch (error) {
//       console.error('Error:', error);
//     }
//   });
// });