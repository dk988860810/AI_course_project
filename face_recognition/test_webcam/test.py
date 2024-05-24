# os.makedirs(current_face_dir)
import os

# 假设 current_face_dir 已经通过上面的代码创建了
new_subfolder = os.path.join('123', "123")
print(new_subfolder)
os.makedirs(new_subfolder, exist_ok=True)