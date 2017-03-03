import numpy as np
import struct
import sys
import multiprocessing

def ibm2ieee2(ibm_float):
    """
    ibm2ieee2(ibm_float)
    Used by permission
    (C) Secchi Angelo
    with thanks to Howard Lightstone and Anton Vredegoor. 
    """
    dividend=float(16**6)
    
    if ibm_float == 0:
        return 0.0
    istic,a,b,c=struct.unpack('>BBBB',ibm_float)
    if istic >= 128:
        sign= -1.0
        istic = istic - 128
    else:
        sign = 1.0
    mant= float(a<<16) + float(b<<8) +float(c)
    return sign* 16**(istic-64)*(mant/dividend)
def convert2int(ibm_data):
    unpack_data = struct.unpack('i',ibm_data)
    d3 = (unpack_data[0] << 24) & 0xff000000
    d2 = (unpack_data[0] << 8) & 0x00ff0000
    d1 = (unpack_data[0] >> 8) & 0x0000ff00
    d0 = (unpack_data[0] >> 24) & 0x000000ff
    val = d3 | d2 | d1 | d0
    return val
def get_data(file_name, hrz, sample_num, min_inline, max_inline, min_xline, max_xline, up_points, down_points, q):
    print(file_name, 'begins')
    pre_data = np.zeros([(max_inline-min_inline+1),(max_xline-min_xline+1),24])
    fp = open(file_name,'rb')
    fp.seek(3600,0)
    for i in range(max_inline-min_inline+1):
        for j in range(max_xline-min_xline+1):
            while(1):
                fp.seek(180,1)
                ibm_data = fp.read(4)
                inline = convert2int(ibm_data)
                ibm_data = fp.read(4)
                xline = convert2int(ibm_data)
                fp.seek(52,1)
                if (inline == (i+min_inline)) and (xline == (j+min_xline)):
                    time = int(hrz[(min_inline-start_inline+i),(min_xline-start_xline+j)])
                    data = fp.read(sample_num*4)
                    trace_data = []
                    for k in range(sample_num):
                        index_begin = k*4
                        index_end = (k+1)*4
                        trace_data.append(ibm2ieee2(data[index_begin:index_end]))
                    pre_data[i,j,:] = trace_data[(time+up_points):(time+down_points)]
                    break
                else:
                    fp.seek(sample_num*4,1)
    fp.close()
    q.put(pre_data)
    print(file_name, 'has been processed')
if __name__ == '__main__':
    start_inline = 66
    end_inline = 865
    start_xline = 535
    end_xline = 1319
    num_inline = end_inline - start_inline + 1
    num_xline = end_xline - start_xline + 1
    min_inline = 101
    max_inline = 800
    #max_inline = 220
    min_xline = 601
    max_xline = 1200
    #max_xline = 620
    
    hrz = np.zeros([num_inline,num_xline])
    
    for line in open('hrz.txt'):
        line_arr = line.strip().split()
        hrz[(int(line_arr[1])-start_inline),(int(line_arr[0])-start_xline)] = round(float(line_arr[4]))
    
    q = multiprocessing.Manager().Queue()
    files = []
    files.append('MIG_azimuth030_060_210_240AGC.segy')
    files.append('MIG_azimuth060_090_240_270AGC.segy')
    files.append('MIG_azimuth000_030_180_210AGC.segy')
    files.append('MIG_azimuth090_120_270_300AGC.segy')
    files.append('MIG_azimuth120_150_300_330AGC.segy')
    files.append('MIG_azimuth150_180_330_360AGC.segy')
    file_num = 6
    up_points = -11
    down_points = 13
    points_num = down_points - up_points
    p = []
    for i in range(file_num):
        p.append(multiprocessing.Process(target = get_data, args = (files[i] ,hrz, 2001, min_inline, max_inline, min_xline, max_xline, up_points, down_points, q)))

    for i in range(file_num):
        p[i].start()
    
    for i in range(file_num):
        p[i].join()

    print('all data have been processed')
    single_data = []

    for i in range(file_num):
        if q.empty():
            print('******Queue is empty!******')
        assert not q.empty()
        single_data.append(q.get())
    
    processed_data = np.zeros([(max_inline-min_inline+1),(max_xline-min_xline+1),(points_num*file_num)])
    for i in range(max_inline-min_inline+1):
        for j in range(max_xline-min_xline+1):
            for k in range(file_num):
                processed_data[i,j,(points_num*k):(points_num*(k+1))]    = single_data[k][i,j,:]
            
    print('merging is done')
    np.save('6positions_24points.npy', processed_data)
    
    #post_data = get_data('PSTM_STK_ALL_AGC.segy', hrz, 2001, min_inline, max_inline, min_xline, max_xline)
    #np.save('post_data.npy', post_data)
    
    
    
