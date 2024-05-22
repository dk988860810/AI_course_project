// HTML DOM 元素
const employeeList = document.getElementById('employeeList');
const addEmployeeBtn = document.getElementById('addEmployeeBtn');
const addEmployeeModal = document.getElementById('addEmployeeModal');
const addEmployeeForm = document.getElementById('addEmployeeForm');
const cancelAddEmployeeBtn = document.getElementById('cancelAddEmployee');
const editModal = document.getElementById('editModal');
const editEmployeeForm = document.getElementById('editEmployeeForm');
const editNameInput = document.getElementById('editName');
const editJobTitleInput = document.getElementById('editJobTitle');
const editDepartmentInput = document.getElementById('editDepartment');
const editLocationInput = document.getElementById('editLocation');
const editPhoneInput = document.getElementById('editPhone');
const editEmergencyContactInput = document.getElementById('editEmergencyContact');
const editEmergencyPhoneInput = document.getElementById('editEmergencyPhone');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const currentPageSpan = document.getElementById('currentPage');

// 員工資料
let employees = [];
const itemsPerPage = 10;
let currentPage = 1;

// 初始化
function initialize() {
  addEmployeeBtn.addEventListener('click', showAddEmployeeModal);
  cancelAddEmployeeBtn.addEventListener('click', hideAddEmployeeModal);
  editEmployeeForm.addEventListener('submit', editEmployee);
  prevPageBtn.addEventListener('click', prevPage);
  nextPageBtn.addEventListener('click', nextPage);
  editModal.addEventListener('click', e => {
    if (e.target === editModal) {
      hideEditModal();
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
  const personalFiles = addEmployeeForm.elements.personalFiles.value;
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
  renderEmployeeList();
  hideAddEmployeeModal();
}

// 顯示編輯員工弹出窗口
function showEditModal(employee) {
  document.getElementById('editId').value = employee.id;
  document.getElementById('editName').value = employee.name;
  document.getElementById('editJobTitle').value = employee.jobTitle;
  document.getElementById('editDepartment').value = employee.department;
  document.getElementById('editLocation').value = employee.location;
  document.getElementById('editPhone').value = employee.phone;
  document.getElementById('editEmergencyContact').value = employee.emergencyContact;
  document.getElementById('editEmergencyPhone').value = employee.emergencyPhone;
  editModal.style.display = 'block';
}

// 隱藏編輯員工弹出窗口
function hideEditModal() {
  editModal.style.display = 'none';
}

// 編輯員工
function editEmployee(event) {
  event.preventDefault();
  const id = document.getElementById('editId').value;
  const employee = employees.find(e => e.id == id);
  if (employee) {
    employee.name = document.getElementById('editName').value;
    employee.jobTitle = document.getElementById('editJobTitle').value;
    employee.department = document.getElementById('editDepartment').value;
    employee.location = document.getElementById('editLocation').value;
    employee.phone = document.getElementById('editPhone').value;
    employee.emergencyContact = document.getElementById('editEmergencyContact').value;
    employee.emergencyPhone = document.getElementById('editEmergencyPhone').value;
  }
  renderEmployeeList();
  hideEditModal();
}

// 渲染員工列表
function renderEmployeeList() {
  const employeeList = document.getElementById('employeeList');
  employeeList.innerHTML = '';
  const pageEmployees = employees.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  pageEmployees.forEach(employee => {
    const listItem = document.createElement('li');
    listItem.textContent = `${employee.name} - ${employee.jobTitle}`;
    listItem.addEventListener('click', () => showEditModal(employee));
    employeeList.appendChild(listItem);
  });
  updatePagination();
}

// 更新分页
function updatePagination() {
  const totalPages = Math.ceil(employees.length / itemsPerPage);
  currentPageSpan.textContent = `Page ${currentPage} of ${totalPages}`;
  prevPageBtn.disabled = currentPage === 1;
  nextPageBtn.disabled = currentPage === totalPages;
}

// 上一页
function prevPage() {
  if (currentPage > 1) {
    currentPage--;
    renderEmployeeList();
  }
}

// 下一页
function nextPage() {
  const totalPages = Math.ceil(employees.length / itemsPerPage);
  if (currentPage < totalPages) {
    currentPage++;
    renderEmployeeList();
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const closeButton = document.querySelector('.close');
  closeButton.addEventListener('click', function() {
    const modal = document.getElementById('editModal');
    modal.style.display = 'none';
  });
});


document.addEventListener('DOMContentLoaded', function() {
  const editButtons = document.querySelectorAll('.edit-btn');
  const deleteButtons = document.querySelectorAll('.delete-btn');

  editButtons.forEach(button => {
    button.addEventListener('click', function() {
      const row = this.closest('tr');
      const data = {
        id: row.querySelector('.edit-btn').dataset.employeeId,
        name: row.children[1].innerText,
        position: row.children[2].innerText,
        department: row.children[3].innerText,
        location: row.children[4].innerText,
        phone: row.children[5].innerText,
        emergency_contact: row.children[6].innerText,
        emergency_phone: row.children[7].innerText
      };

      fetch('/update_employee', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          alert('更新成功');
        } else {
          alert('更新失敗');
        }
      });
    });
  });

  deleteButtons.forEach(button => {
    button.addEventListener('click', function() {
      const id = this.dataset.employeeId;

      fetch('/delete_employee', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: id })
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          alert('刪除成功');
          location.reload();
        } else {
          alert('刪除失敗');
        }
      });
    });
  });
});
