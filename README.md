# SWEng-Project

-----更新日期：2025/05/31-----

1.主页面的所有功能均可以使用

2.chrome扩展程序已能接收到用户信息及简历信息，接下来在页面实现评分与JD获取即可

-----更新日期：2025/05/30-----

1.优化了简历的视图效果，同时完善了下载和删除效果，查看效果目前仍在排查bug中


backend

1.登陆有效期改到7天

2.POST/api/v1/matching/match-resumes中jd_text和jd_id任选其一即可，数据库中会暂存jd（24h）

3.POST/api/v1/matching/suggestions中jd_text和jd_id任选其一即可，resume_text_to_analyze可以不填

-----更新日期：2025/05/28-----

1.初步设计main页面的内容，之后需要美化主页，并实现各个功能

-----更新日期：2025/05/27-----

1.目前已能够成功从扩展程序跳转到登陆页面，若已登录则会直接跳转到主界面

2.更新了扩展程序的样式，让它变得更好看了

3.目前创建账户功能已实现，能在create account里将账户添加到数据库中，但是登录时无法使用用户名登录，只能使用邮箱

4.下一步是优化补全侧边栏界面及主页面

-----更新日期：2025/05/26-----

1.补全登录界面和账号注册页面，目前登录页面已连接后端及数据库，仍需确保注册能正常使用

-----更新日期：2025/05/22-----


1.新增简历匹配和llm建议功能

2.计划(5.23)：优化简历匹配算法，优化llm-prompt，编写api文档


后端待做：

1.构建/找测试简历库（300-500份）

2.测试：各项api功能，matching/suggestion时间

3.部署


-----更新日期：2025/05/16-----

1.侧边栏内容新增评分栏及JD分区，修改了侧边栏中的部分样式

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
