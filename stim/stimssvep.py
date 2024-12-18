# -*- coding: utf-8 -*-


# load in basic modules
import os
import string
import sys
import tkinter
import numpy as np
import scipy.io as io
from math import pi
from psychopy import (core, data, visual, event)
import socket
import serial

# from ex_base import NeuroScanPort
# AA 25  出现的什么  第几次出现 BB
# AA 25 00 01 BB
hex_string = "AA 25 00 01 00 BB"
hex_data = bytearray.fromhex(hex_string)
sw = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H'}
SWI = {0: 0x41, 1: 0x42, 2: 0x43, 3: 0x44, 4: 0x45, 5: 0x46, 6: 0x47, 7: 0x48}

OnceStimulateNum = 8
# Master_Lable = 1
# Lable_COM = "COM7"


# prefunctions
def sinusoidal_sample(freqs, phases, srate, frames, colors=[1, 1, 1]):
    """Sinusoidal approximate sampling method.

    Args:
        freqs (list of float): Frequencies of each stimulus.
        phases (list of float): Phases of each stimulus.
        srate (int or float): Refresh rate of screen.
        frames (int): Flashing frames.

    Returns:
        color (ndarray): (n_frames, n_elements, 3)
    """
    time = np.linspace(0, (frames - 1) / srate, frames)
    color = np.zeros((frames, len(freqs), 3))
    for ne, (freq, phase) in enumerate(zip(freqs, phases)):
        temp = np.sin(2 * pi * freq * time + pi * phase)
        color_rgb = [[] for i in range(3)]
        for i in range(frames):
            color_rgb[0].append(temp[i] >= 0 and colors[0] or -1)
            color_rgb[1].append(temp[i] >= 0 and colors[1] or -1)
            color_rgb[2].append(temp[i] >= 0 and colors[2] or -1)
        sinw1 = np.array(color_rgb[0])
        sinw2 = np.array(color_rgb[1])
        sinw3 = np.array(color_rgb[2])
        # print(sinw1)
        # print(len(sinw1))
        color[:, ne, :] = np.vstack((sinw1, sinw2, sinw3)).T
    return color


def square_sample(freqs, phases, duty_cycle, srate, frames):
    pass


# create interface for VEP-BCI-Speller
class KeyboardInterface(object):
    """Create stimulus interface."""

    def __init__(self, win_size=[1920, 1080], color=[-1, -1, -1], colorSpace='rgb',
                 fullscr=True, allowGUI=True, monitor=None, screen=0):
        """Config Window object.

        Args:
            win_size (array-like of int): Size of the window in pixels [x, y].
            color (array-like of float): Normalized color of background as [r, g, b] list or single value.
                Defaults to pure black [-1.0, -1.0, -1.0].
            colorSpace (str): Defaults to 'rgb'.
            fullscr (bool): Create a window in 'full-screen' mode to achieve better timing.
            allowGUI (bool): Allow window to be drawn with frames and buttons to close.
            monitor (monitor): The monitor to be used during the experiment.
                Set None to use default profile.
            screen (int): Specifies the physical screen that stimuli will appear on.
                Values can be >0 if more than one screen is present.
        """
        # config Window object
        if fullscr:
            win_size = [tkinter.Tk().winfo_screenwidth(), tkinter.Tk().winfo_screenheight()]
        self.win = visual.Window(size=win_size, color=color, colorSpace=colorSpace, fullscr=fullscr,
                                 allowGUI=allowGUI, monitor=monitor, screen=screen)
        self.win.mouseVisible = False
        event.globalKeys.add(key='escape', func=self.win.close)  # press 'esc' to quit
        self.win_size = np.array(win_size)  # e.g. [1920,1080]
        prepare = visual.TextStim(win=self.win, text="Press space to begin!", color=[1, 1, 1])
        prepare.draw()
        self.win.flip()
        event.waitKeys(keyList='space')

    def config_pos(self, n_elements=40, rows=5, columns=8, stim_pos=None, stim_length=150, stim_width=150):
        """Config positions of stimuli.

        Args:
            n_elements (int): Number of stimuli.
            rows (int, optional): Rows of keyboard.
            columns (int, optional): Columns of keyboard.
            stim_pos (ndarray, optional): Extra position matrix.
            stim_length (int): Length of stimulus.
            stim_width (int): Width of stimulus.

        Raises:
            Exception: Inconsistent numbers of stimuli and positions.
        """
        self.n_elements = n_elements
        # highly customizable position matrix
        if (stim_pos is not None) and (self.n_elements == stim_pos.shape[0]):
            # note that the origin point of the coordinate axis should be the center of your screen
            # (so the upper left corner is in Quadrant 2nd), and the larger the coordinate value,
            # the farther the actual position is from the center
            self.stim_pos = stim_pos
        # conventional design method
        elif (stim_pos is None) and (rows * columns >= self.n_elements):
            # according to the given rows of columns, coordinates will be automatically converted
            stim_pos = np.zeros((self.n_elements, 2))
            # divide the whole screen into rows*columns' blocks, and pick the center of each block
            first_pos = np.array([self.win_size[0] / columns, self.win_size[1] / rows]) / 2
            if (first_pos[0] < stim_length / 2) or (first_pos[1] < stim_width / 2):
                raise Exception('Too much blocks or too big the stimulus region!')
            for i in range(columns):
                for j in range(rows):
                    stim_pos[i * rows + j] = first_pos + [i, j] * first_pos * 2
            # note that those coordinates are still not the real ones that need to be set on the screen
            stim_pos -= self.win_size / 2  # from Quadrant 1st to 3rd
            stim_pos[:, 1] *= -1  # invert the y-axis
            self.stim_pos = stim_pos
        else:
            raise Exception('Incorrect number of stimulus!')

        # check size of stimuli
        stim_sizes = np.zeros((self.n_elements, 2))
        stim_sizes[:] = np.array([stim_length, stim_width])

        self.stim_sizes = stim_sizes
        self.stim_width = stim_width
        self.response_pos = np.zeros((2))

    def config_text(self, symbols=None, symbol_height=0):
        """Config text stimuli.

        Args:
            symbols (list of str): Target characters.
            symbol_height (int): Height of target symbol.

        Raises:
            Exception: Insufficient characters.
        """
        # check number of symbols
        if (symbols is not None) and (len(symbols) >= self.n_elements):
            self.symbols = symbols
        elif self.n_elements <= 40:
            self.symbols = ''.join([string.ascii_uppercase, '1234567890+-*/'])
        else:
            raise Exception('Please input correct symbol list!')

        # add text targets onto interface
        if symbol_height == 0:
            symbol_height = self.stim_width / 2
        self.text_stimuli = []
        for symbol, pos in zip(self.symbols, self.stim_pos):
            self.text_stimuli.append(visual.TextStim(win=self.win, text=symbol, font='Times New Roman', pos=pos,
                                                     color=[1., 1., 1.], units='pix', height=symbol_height, bold=True,
                                                     name=symbol))
        for text_stimulus in self.text_stimuli:
            text_stimulus.draw()
        self.win.flip()


# config visual stimuli
class VisualStim(KeyboardInterface):
    """Create various visual stimuli."""

    def __init__(self, win_size=[1920, 1080], color=[-1, -1, -1], colorSpace='rgb',
                 fullscr=True, allowGUI=True, monitor=None, screen=0):
        super().__init__(win_size, color, colorSpace, fullscr, allowGUI, monitor, screen)

    def config_color(self, stim_frames, stim_colors, **kwargs):
        """Config color of stimuli.

        Args:
            stim_frames (int): Flash frames of one trial.
            stim_colors (ndarray): (n_frames, n_elements, 3).

        Raises:
            Exception: Inconsistent frames and color matrices.
        """
        # check consistency
        incorrect_frame = (stim_colors.shape[0] != stim_frames)
        incorrect_number = (stim_colors.shape[1] != self.n_elements)
        if incorrect_frame or incorrect_number:
            raise Exception('Incorrect color matrix or flash frames!')

        # initialize extra inputs
        self.stim_colors = stim_colors  # color
        self.stim_frames = stim_frames  # time
        self.stim_oris = np.zeros((self.n_elements,))  # orientation
        self.stim_sfs = np.zeros((self.n_elements,))  # spatial frequency
        self.stim_contrs = np.zeros((self.n_elements,))  # contrast
        self.stim_opacities = np.zeros((self.n_elements,))  # opacity
        self.stim_phases = np.zeros((self.n_elements,))  # phase

        # check extra inputs
        if 'stim_oris' in kwargs.keys():
            self.stim_oris = kwargs['stim_oris']
        if 'stim_sfs' in kwargs.keys():
            self.stim_sfs = kwargs['stim_sfs']
        if 'stim_contrs' in kwargs.keys():
            self.stim_contrs = kwargs['stim_contrs']
        if 'stim_opacities' in kwargs.keys():
            self.stim_opacities = kwargs['stim_opacities']
        if 'stim_phases' in kwargs.keys():
            self.stim_phases = kwargs['stim_phases']

        # add flashing targets onto interface
        self.flash_stimuli = []
        for sf in range(self.stim_frames):
            self.flash_stimuli.append(visual.ElementArrayStim(win=self.win, units='pix', nElements=self.n_elements,
                                                              sizes=self.stim_sizes, xys=self.stim_pos,
                                                              colors=self.stim_colors[sf, ...],
                                                              opacities=self.stim_opacities,
                                                              oris=self.stim_oris, sfs=self.stim_sfs,
                                                              contrs=self.stim_contrs,
                                                              phases=self.stim_phases, elementTex=np.ones((64, 64)),
                                                              elementMask=None, texRes=48))

    def config_index(self, index_height=0):
        """Config index stimuli: downward triangle (Unicode: \u2BC6)

        Args:
            index_height (int, optional): Defaults to 75 pixels.
        """
        # add index onto interface, with positions to be confirmed.
        if index_height == 0:
            index_height = self.stim_width / 2
        self.index_stimuli = visual.TextStim(win=self.win, text='\u2BC6', font='Arial', color=[1., 1., 0.],
                                             colorSpace='rgb', units='pix', height=index_height, bold=True,
                                             autoLog=False)

    def config_response(self, text_height=0, response='A'):
        """Config index stimuli: downward triangle (Unicode: \u2BC6)
        Args:
            index_height (int, optional): Defaults to 75 pixels.
        """
        self.response = '0'
        # add index onto interface, with positions to be confirmed.
        text_height = self.stim_width
        self.text_response = visual.TextStim(win=self.win, text=self.response, font='Times New Roman',
                                             pos=self.response_pos,
                                             color=[1., 1., 1.], units='pix', height=text_height, bold=True)


# standard SSVEP paradigm
class SSVEP(VisualStim):
    """Create SSVEP stimuli."""

    def __init__(self, win_size=[1920, 1080], color=[-1, -1, -1], colorSpace='rgb',
                 fullscr=True, allowGUI=True, monitor=None, screen=0, freqs=None, phases=None):
        """Item class from VisualStim.

        Args:
            freqs (list of float): Frequencies of each stimulus.
            phases (list of float): Phases of each stimulus.
        """
        super().__init__(win_size, color, colorSpace, fullscr, allowGUI, monitor, screen)
        self.freqs = freqs
        self.phases = phases

    def config_color(self, refresh_rate=0, flash_time=0, stim_color=[1, 1, 1], stimtype='sinusoid'):
        self.flash_stimuli = flash_time
        self.refresh_rate = refresh_rate
        if refresh_rate == 0:
            self.refresh_rate = np.floor(self.win.getActualFrameRate(nIdentical=20, nWarmUpFrames=20))
        self.stim_frames = int(flash_time * self.refresh_rate)
        if (stimtype == 'sinusoid'):
            self.stim_colors = sinusoidal_sample(freqs=self.freqs, phases=self.phases,
                                                 srate=self.refresh_rate, frames=self.stim_frames, colors=stim_color)
            if (self.stim_colors[0].shape[0] != self.n_elements):
                raise Exception('Please input correct num of stims!')

                # add flashing targets onto interface
        self.flash_stimuli = []
        for sf in range(self.stim_frames):
            self.flash_stimuli.append(visual.ElementArrayStim(win=self.win, units='pix', nElements=self.n_elements,
                                                              sizes=self.stim_sizes, xys=self.stim_pos,
                                                              colors=self.stim_colors[sf, ...],
                                                              elementTex=np.ones((64, 64)), elementMask=None,
                                                              texRes=48))  # nElements=self.n_elements,


# standard P300 paradigm
class P300(VisualStim):
    """Create P300 stimuli."""

    def __init__(self, win_size=[1920, 1080], color=[-1, -1, -1], colorSpace='rgb', fullscr=True, allowGUI=True,
                 monitor=None,
                 screen=0):
        super().__init__(win_size, color, colorSpace, fullscr, allowGUI, monitor, screen)

    def config_color(self, refresh_rate=0, symbol_height=0, stim_duration=0.5):
        self.stim_duration = stim_duration
        self.refresh_rate = refresh_rate
        if refresh_rate == 0:
            self.refresh_rate = np.floor(self.win.getActualFrameRate(nIdentical=20, nWarmUpFrames=20))

        # highlight one row/ column onto interface
        row_pos = np.unique(self.stim_pos[:, 0])
        col_pos = np.unique(self.stim_pos[:, 1])
        [row_num, col_num] = [len(col_pos), len(row_pos)]
        self.stim_frames = int((row_num + col_num) * stim_duration * refresh_rate)  # complete single trial

        row_order_index = list(range(0, row_num))
        np.random.shuffle(row_order_index)
        col_order_index = list(range(0, col_num))
        np.random.shuffle(col_order_index)

        # Determine row and column char status
        stim_colors_row = np.zeros([(row_num * col_num), int(row_num * refresh_rate * stim_duration), 3])
        stim_colors_col = np.zeros([(row_num * col_num), int(col_num * refresh_rate * stim_duration), 3])  #

        tmp = 0
        for col_i in col_order_index:
            stim_colors_col[(col_i * row_num):((col_i + 1) * row_num),
            int(tmp * refresh_rate * stim_duration):int((tmp + 1) * refresh_rate * stim_duration)] = [-1, -1, -1]
            tmp += 1

        tmp = 0
        for row_i in row_order_index:
            for col_i in range(col_num):
                stim_colors_row[(row_i + row_num * col_i),
                int(tmp * refresh_rate * stim_duration):int((tmp + 1) * refresh_rate * stim_duration)] = [-1, -1, -1]
            tmp += 1

        stim_colors = np.concatenate((stim_colors_row, stim_colors_col), axis=1)
        self.stim_colors = np.transpose(stim_colors, [1, 0, 2])

        # add flashing targets onto interface
        self.flash_stimuli = []
        for sf in range(self.stim_frames):
            self.flash_stimuli.append(visual.ElementArrayStim(win=self.win, units='pix', nElements=self.n_elements,
                                                              sizes=self.stim_sizes, xys=self.stim_pos,
                                                              colors=self.stim_colors[sf, ...],
                                                              elementTex=np.ones((64, 64)), elementMask=None,
                                                              texRes=48))

        # Adjust character grayscale
        if symbol_height == 0:
            symbol_height = self.stim_width / 2
        self.text_stimuli = []
        for symbol, pos in zip(self.symbols, self.stim_pos):
            self.text_stimuli.append(visual.TextStim(win=self.win, text=symbol, font='Times New Roman', pos=pos,
                                                     color=[1, 1, 1], units='pix', height=symbol_height, bold=True,
                                                     name=symbol))


# basic experiment control
class Experiment(object):
    def __init__(self, display_time=1., index_time=1., rest_time=0.5, respond_time=0, sever_port=9045, nrep=1):
        """Passing outsied parameters to inner attributes.

        Args:
            display_time (float): Keyboard display time before 1st index.
            index_time (float): Indicator display time.
            rest_time (float, optional): Rest-state time.
            respond_time (float, optional): Feedback time during online experiment.
        """
        self.display_time = display_time
        self.index_time = index_time
        self.rest_time = rest_time
        self.respond_time = respond_time
        self.sever_port = sever_port
        self.nrep = nrep
        # self.ser = serial.Serial("COM16", 115200, timeout=1)


    def run(self, VSObject):
        # config experiment settings
        CNT = 0
        conditions = [{'id': i} for i in range(VSObject.n_elements)]
        trials = data.TrialHandler(conditions, self.nrep, name='experiment', method='sequential')
        routine_timer = core.CountdownTimer()
        receive_msg_port = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receive_msg_port.bind(('', self.sever_port))  # 服务器的地址和端口

        # start routine
        # episode 1: display speller interface
        routine_timer.reset(0)
        routine_timer.add(self.display_time)
        while routine_timer.getTime() > 0:
            for text_stimulus in VSObject.text_stimuli:
                text_stimulus.draw()
            VSObject.win.flip()

        # episode 2: begin to flash
        for trial in trials:
            # initialise index position
            id = int(trial['id'])
            # print(id)
            position = VSObject.stim_pos[id] + np.array([0, VSObject.stim_width / 2])
            VSObject.index_stimuli.setPos(position)

            # # initialise response   这里注释掉了
            # receive_msg, receive_address = receive_msg_port.recvfrom(1024)
            # receive_msg = receive_msg.decode('utf-8') # 信息格式进行转化
            # print('Receive message:', receive_msg)
            # VSObject.text_response.setText(receive_msg)

            ## phase I: speller & index (eye shifting)
            routine_timer.reset(0)
            routine_timer.add(self.index_time)
            while routine_timer.getTime() > 0:
                for text_stimulus in VSObject.text_stimuli:
                    text_stimulus.draw()
                VSObject.index_stimuli.draw()
                VSObject.win.flip()

            # phase II: rest state
            if self.rest_time != 0:
                routine_timer.reset(0)
                routine_timer.add(self.rest_time)
                while routine_timer.getTime() > 0:
                    for text_stimulus in VSObject.text_stimuli:
                        text_stimulus.draw()
                    VSObject.win.flip()

            hex_data[2] = hex_data[2] + SWI[id]
            if CNT == 0:
                hex_data[3] = hex_data[3]
            else:
                hex_data[3] = hex_data[3] + int(CNT / OnceStimulateNum)
            # if Master_Lable:
            # self.ser.write(hex_data)
            print(hex_data)
            print("\n\n")
            print(sw[id])
            print("\n\n")
            print(CNT)
            print("\n\n")
            hex_data[2] = 0
            hex_data[3] = 1

            CNT += 1
            # print(port.sendLabel)
            # phase III: target stimulating
            # win.callOnFlip(port.sendLabel, id+1)
            for sf in range(VSObject.stim_frames):
                VSObject.flash_stimuli[sf].draw()
                # !!!  notice P300 !!!
                for text_stimulus in VSObject.text_stimuli:
                    text_stimulus.draw()
                # !!!
                VSObject.win.flip()

            # phase IV: respond
            if self.respond_time != 0:
                routine_timer.reset(0)
                routine_timer.add(self.respond_time)
                while routine_timer.getTime() > 0:
                    VSObject.text_response.draw()
                    VSObject.win.flip()
        VSObject.win.close()
        core.quit()


# 参数 频率，闪烁时间，框大小,次数,屏幕分辨率
def SSVEPWork (FrequsStart ,FrequsEnd ,FlashTime ,Size, Num, RefreshRate):
    freqs = [i for i in range(FrequsStart, FrequsEnd)]

    phases = [0.5 for i in range(8)]

    '''
    SSVEP初始化常用参数：win_size确定范式边框大小（像素表示），默认[1920,1080]; color确定背景颜色[-1~1,-1~1,-1~1]； fullscr，True全窗口，
    此时win_size参数默认屏幕分辨率;freqs频率(数目应于刺激块数目一致);phases相位;    space开始，esc退出
    '''
    ssvep40 = SSVEP(win_size=[1920, 1080], fullscr=True, color=[-1, -1, -1], freqs=freqs, phases=phases)
    '''
    config_pos,设置函数确定刺激和符号位置大小等。  常用参数：n_elements刺激块数目; row为行数; columns为列数; stim_pos为自定义刺激块位置(默认
    为None,由行数和列数确定);二维数组表示[[-150,150],...]; stim_length和stim_width为刺激块边长; symbols为自定义符号(默认为ABC...);
    symbols_height为符号高度(默认stim_width/2)
    '''
    ssvep40.config_pos(n_elements=8, rows=2, columns=4, stim_length=Size, stim_width=Size)
    ssvep40.config_text()
    '''
    config_color设置刺激块频率刷新率等。   常用参数：refresh_rate刷新率; flash_time刺激块闪烁时间; stim_color设置闪烁颜色
    '''
    ssvep40.config_color(refresh_rate=RefreshRate, flash_time=FlashTime, stim_color=[1, 1, 1])

    '''
    config_index设置刺激提示。  参数：index_height提示块大小(默认stim_width/2) 提示快形状为倒三角，目前不能更改
    '''
    ssvep40.config_index()

    '''
    '''
    # ssvep40.config_response()

    '''
    Experiment初始化参数：display_tim按键开始后延迟时间; index_time提示时间; rest_time休息时间？;respond_time响应时间; sever_port
    地址; nrep轮次
    '''
    experiment = Experiment(index_time=1, rest_time=1, nrep=Num)
    experiment.run(ssvep40)


# FrequsStart与FrequsEnd相差OnceStimulateNum
# 参数 频率，闪烁时间，框大小,次数,屏幕分辨率
SSVEPWork(FrequsStart=4, FrequsEnd=12, FlashTime=5, Size=200, Num=1, RefreshRate=60)
hu


'''
P300 初始化
'''
# P300_40 = P300(win_size= [1650,1050], fullscr=False, color=[0,0,0])
# P300_40.config_pos(n_elements=40, rows=5, columns=8)
# P300_40.config_text()
# P300_40.config_color(refresh_rate=120,stim_duration=0.3)
# P300_40.config_index()
# experiment = Experiment()
# experiment.run(P300_40)
