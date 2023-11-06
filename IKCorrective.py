# coding=utf-8
'''
创建在MAYA中用于矫正角色胳膊肘以及膝盖等肢体关节在FK模式下，进行动捕数据匹配时，造成的胳膊肘等多轴旋转从而导致关节处修型扭曲跳变等现象
利用IK关节原理，将胳膊肘处的多轴旋转数值转换为单轴旋转，并始终保持单轴旋转，确保胳膊肘等部位的修型形态保持

python ：version 3.7.7 64bit
ver 1.0
author ： Chuan Qin
'''
import maya.cmds as cmds
import maya.mel as mel

class main:
    def __init__(self):

        self.winID = 'IK_corrective'
        self.title = 'IK Corrective Tools'
        self.system_grp = 'IKCorrective_system_grp'
        self.ikHandle = 'ikHandle_grp'
        self.locator = 'locator_grp'


    def ui_win(self):
        if cmds.window(self.winID, exists = True):
            cmds.deleteUI(self.winID, wnd = True)
        
        winUI = cmds.window(self.winID, title = self.title, wh = (250, 220))
        cmds.columnLayout(adj = 1)
        cmds.text('Using IK to correct elbow or knee joints\n to ensure single axis rotation', al = 'left', h = 30)
        cmds.separator(h = 10, style = 'in')
        cmds.textFieldButtonGrp('parent_tfb', label = 'Parent :', adj = 2, cw3 = (50, 150, 50), buttonLabel = '<<<', buttonCommand = lambda*args:self.load_joints('parent'))
        cmds.textFieldButtonGrp('Shoulder_tfb', label = 'Shoulder :', adj = 2, cw3 = (50, 150, 50), buttonLabel = '<<<', buttonCommand = lambda*args:self.load_joints('Shoulder'))
        cmds.textFieldButtonGrp('Elbow_tfb', label = 'Elbow :', adj = 2, cw3 = (50, 150, 50), buttonLabel = '<<<', buttonCommand = lambda*args:self.load_joints('Elbow'))
        cmds.textFieldButtonGrp('Hand_tfb', label = 'Hand :', adj = 2, cw3 = (50, 150, 50), buttonLabel = '<<<', buttonCommand = lambda*args:self.load_joints('Hand'))
        cmds.separator(h = 10, style = 'in')
        cmds.separator(h = 10, style = 'in')
        cmds.button(label = 'Creat ikCorrective', h = 40, command = lambda*args:self.creat_connection())

        cmds.setParent('..')
        cmds.showWindow(winUI)

    def load_joints(self, obj):
        # 加载选择的骨骼或者FK控制器
        sel = cmds.ls(sl = True)[0]
        cmds.textFieldButtonGrp('{}_tfb'.format(obj), edit = True, text = sel)

    def get_joints_name(self):
        # 获取所选择的关节或FK控制器名称
        objs = ['Shoulder', 'Elbow', 'Hand']
        joint_names = list()
        for obj in objs:
            name = cmds.textFieldButtonGrp('{}_tfb'.format(obj), query = True, text = True)
            joint_names.append(name)

        return joint_names
    
    def get_parent(self):
        parent = cmds.textFieldButtonGrp('parent_tfb', query = True, text = True)
        return parent

    def creat_replace_joints(self):
        # 创建一个替代关节，替代原有关节，保持原有关节层级等不变
        
        if cmds.objExists(self.system_grp):
            system_grp = self.system_grp
        else:
            system_grp = cmds.group(name = self.system_grp, empty = True)

        joints = self.get_joints_name()

        replace_grp = cmds.group(name = '{}_replace_joints_grp'.format(joints[1]), empty = True)
        cmds.setAttr('{}.v'.format(replace_grp), 0)
        cmds.matchTransform(replace_grp, joints[0])
        
        replace_joints_list = list()

        for joint in joints:
            re_joint = cmds.joint(p = (0,0,0), name = '{}_replace_jnt'.format(joint))
            cmds.joint('{}_replace_jnt'.format(joint),edit = True, zso = True)
            cmds.matchTransform(re_joint, joint)
            cmds.select(cl = True)
            replace_joints_list.append(re_joint)

        cmds.parent(replace_joints_list[2], replace_joints_list[1])
        cmds.parent(replace_joints_list[1], replace_joints_list[0])
        cmds.parent(replace_grp, system_grp)

        cmds.select(replace_joints_list[0], hi = True)
        mel.eval('channelBoxCommand -freezeRotate')

        cmds.select(cl = True)
        return  replace_joints_list, replace_grp

    def creat_driver_joints(self):
        # 创建驱动关节，用来驱动并矫正替代关节

        if cmds.objExists(self.system_grp):
            system_grp = self.system_grp
        else:
            system_grp = cmds.group(name = self.system_grp, empty = True)

        joints = self.get_joints_name()

        driver_grp = cmds.group(name = '{}_driver_joints_grp'.format(joints[1]), empty = True)
        cmds.setAttr('{}.v'.format(driver_grp), 0)
        
        cmds.matchTransform(driver_grp, joints[0])
        
        driver_joints_list = list()

        for joint in joints:
            dri_joint = cmds.joint(p = (0,0,0), name = '{}_driver_jnt'.format(joint))
            cmds.joint('{}_driver_jnt'.format(joint),edit = True, zso = True)
            cmds.matchTransform(dri_joint, joint)
            cmds.select(cl = True)
            driver_joints_list.append(dri_joint)

        cmds.parent(driver_joints_list[2], driver_joints_list[1])
        cmds.parent(driver_joints_list[1], driver_joints_list[0])
        cmds.parent(driver_grp, system_grp)

        cmds.select(driver_joints_list[0], hi = True)
        mel.eval('channelBoxCommand -freezeRotate')
        cmds.select(cl = True)

        return driver_joints_list, driver_grp

    def creat_ikHandle(self, joints):
        # 创建所需要的IK

        if cmds.objExists(self.ikHandle):
            ikHandle_grp = self.ikHandle
        else:
            ikHandle_grp = cmds.group(name = self.ikHandle, empty = True)
        ikHandle = cmds.ikHandle(name = '{}_ikHandle'.format(joints[1]), startJoint = joints[0], endEffector = joints[-1], solver = 'ikRPsolver')
        cmds.parent(ikHandle[0], ikHandle_grp)

        parent = cmds.listRelatives(ikHandle_grp, p = True)
        if parent == None:
            cmds.parent(ikHandle_grp, self.system_grp)
        elif parent[0] == self.system_grp:pass
        else:
            cmds.parent(ikHandle_grp, self.system_grp)
        return ikHandle, ikHandle_grp
        
    
    def creat_controlRig(self, joints):
        # 创建driver_joints FK控制器
        grps = list()
        ctrls = list()
        for i in range(len(joints)):
            ctrl = cmds.circle(name = '{}_ctrl'.format(joints[i]), nr = (1,0,0), r = 2 , ch = 0 )
            grp1 = cmds.group(ctrl,name = '{}_Extragrp'.format(ctrl))
            grp2 = cmds.group(grp1, name = '{}_SDKgrp'.format(ctrl))
            grp3 = cmds.group(grp2, name = '{}_offestgrp'.format(ctrl))
            cmds.delete(cmds.parentConstraint((joints[i]), grp3, mo = False))
            cmds.parentConstraint(ctrl , joints[i])
            cmds.scaleConstraint(ctrl , joints[i])
            grps.append(grp3)
            ctrls.append(ctrl)
        
        for i in range(len(ctrls)):
            if i > 0 :
                cmds.parent(grps[i], ctrls[i-1])

        if cmds.objExists(self.system_grp):
            cmds.parent(grps[0], self.system_grp)

        return grps

    def creat_connection(self):
        # 创建连接

        if cmds.objExists(self.system_grp):
            system_grp = self.system_grp
        else:
            system_grp = cmds.group(name = self.system_grp, empty = True)

        joints = self.get_joints_name()
        
        group = cmds.group(name = '{}_ikCorrect_grp'.format(joints[1]), empty = True)
        cmds.parent(group, system_grp)
        
        replace_joints = self.creat_replace_joints()
        driver_joints = self.creat_driver_joints()
        replace_ikHandle = self.creat_ikHandle(replace_joints[0])
        

        if cmds.objExists(self.locator):
            loc_grp = self.locator
        else:
            loc_grp = cmds.group(name = self.locator, empty = True)
        # 创建一个locator用来约束替代关节的ik极向量
        replace_loc = cmds.spaceLocator(name = '{}_poleVector_loc'.format(replace_joints[0][1]))[0]
        cmds.matchTransform(replace_loc, replace_joints[0][1])
        cmds.parent(replace_loc, loc_grp)

        parent = cmds.listRelatives(loc_grp, p = True)
        if parent == None: 
            cmds.parent(loc_grp, self.system_grp)
        elif parent[0] == self.system_grp:pass
        else:
            cmds.parent(loc_grp, self.system_grp)

        # 约束原蒙皮关节
        for i in range(len(joints)):
            cmds.parentConstraint(replace_joints[0][i], joints[i], mo = True)
            cmds.scaleConstraint(replace_joints[0][i], joints[i], mo = True)

        # 替代关节的ik极向量约束
        cmds.poleVectorConstraint(replace_loc, replace_ikHandle[0][0], weight = 1)
        # 驱动关节的手腕点约束替代关节的ikHandle
        cmds.pointConstraint(driver_joints[0][-1], replace_ikHandle[0][0], mo = True)
        # 驱动关节的手腕方向约束替代关节的手腕
        cmds.orientConstraint(driver_joints[0][-1], replace_joints[0][-1], mo = True)
        # 驱动关节的肩关节父子约束极向量loc
        cmds.parentConstraint(driver_joints[0][0], replace_loc, mo = True)

        cmds.setAttr('{}.v'.format(self.ikHandle), 0)
        cmds.setAttr('{}.v'.format(self.locator), 0)

        cmds.select(joints)
        dis_layer_name = '{}_dis_lay'.format(joints[1])
        cmds.createDisplayLayer(name = dis_layer_name, nr = True)
        layer_list = cmds.ls(long = True, type = 'displayLayer')
        layer_index = layer_list.index(dis_layer_name)
        cmds.setAttr('{}.visibility'.format(layer_list[layer_index]), 0)
        # cmds.layerButton(dis_layer_name, edit = True, lv = 0)
        ctrls_grp = self.creat_controlRig(driver_joints[0])

        # 设置父对象约束整体驱动，保证生成的矫正系统能够跟随身体运动
        parent = self.get_parent()
        cmds.parentConstraint(parent, replace_joints[1], mo = True)
        cmds.scaleConstraint(parent, replace_joints[1], mo = True)
        cmds.parentConstraint(parent, ctrls_grp[0], mo = True)
        cmds.scaleConstraint(parent, ctrls_grp[0], mo = True)

        cmds.parent(replace_joints[1], group)
        cmds.parent(driver_joints[1], group)
        cmds.parent(ctrls_grp[0], group)

        


if  __name__ == '__main__':
    temp = main
    temp.ui_win()