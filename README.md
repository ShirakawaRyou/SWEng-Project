# SWEng-Project

-----更新日期：2025/05/11-----

1. 简历管理功能：上传/预览/下载/删除/（缩略图功能未成功，目前不影响，后期再调整）

-----更新日期：2025/05/10-----

已完成：

1.配置和数据库构建

2.用户认证系统（包含用户账户的：注册/登陆/获取用户信息/deactive(软删除)/reactive/delect(硬删除)）

3.侧边栏的内容填充部分及按钮跳转到前端网页

4.用户登录前端界面位于frontend/src/views/login/LoginPage.vue，用户信息界面为主页面记为main，已与插件中的按钮关联

未完成：

1.在chromeExtension/sidebar.js的用户信息跳转按钮处需补充是否登录的API————在设计好API之后直接用于跳转判断

（backend）未完成：

1. 简历管理功能：上传和管理功能

2. 关键词提取和匹配功能：JD/简历提取+解析

3. Gemini API集成，实现简历改进建议功能

4. 编写测试

5. 完善api

6. 部署

-----更新日期：2025/05/08-----

在chromeExtension文件夹下，新增侧边栏，通过点击按钮及插件图标即可展开和收缩右侧侧边栏
之后需要完善侧边栏中的内容，插件的各种icon暂可不考虑

-----更新日期：2025/05/01-----

使用方式：
在Google extension中加载已解压的扩展程序
文件夹为chromeExtension

后端 Python + Django
在backend文件夹下使用 python manage.py runserver

前端 Node.js+Vue3
在frontend文件夹下使用 npm run serve

在chrome中右上角的插件目录中点击按钮即可跳转到localhost:8080/IndexPage页面

页面中为后端输出的内容
