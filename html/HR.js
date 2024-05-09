// 維護和操作員工資料的程式碼

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
      hideEditModal();
    }
  });
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
    personalFiles: personalFiles.split(',').map(file => file.trim()),
  };
  employees.push(newEmployee);
  currentPage = 1;
  startIndex = 0;
  endIndex = itemsPerPage;
  renderEmployeeList();
  hideAddEmployeeModal();
}

// 編輯員工
function editEmployee(event) {
  event.preventDefault();
  const employeeId = event.target.elements.employeeId.value;
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

// 隱藏編輯員工弹出窗口
function hideEditModal() {
  editModal.style.display = 'none';
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
  currentPage--;
  startIndex -= itemsPerPage;
  endIndex -= itemsPerPage;
  renderEmployeeList();
}

// 下一頁
function nextPage() {
  currentPage++;
  startIndex += itemsPerPage;
  endIndex += itemsPerPage;
  renderEmployeeList();
}
