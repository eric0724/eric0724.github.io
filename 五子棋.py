"""
程式名稱：五子棋

"""
xy=[9,0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0,
    0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0,
    0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0,
    0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0,
    0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0 ,0,0,0,0,0]
p = 0
m = 0
def xy1():
         global p
         if p<=1:
                 xy[1]=1
                 x1.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[1]=2
                 x1.config(state=tk.DISABLED,bg = 'black')
def xy2():
         global p
         if p<=1:
                 xy[2]=1
                 x2.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[2]=2
                 x2.config(state=tk.DISABLED,bg = 'black')
def xy3():
         global p
         if p<=1:
                 xy[3]=1
                 x3.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[3]=2
                 x3.config(state=tk.DISABLED,bg = 'black')
def xy4():
         global p
         if p<=1:
                 xy[4]=1
                 x4.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[4]=2
                 x4.config(state=tk.DISABLED,bg = 'black')
def xy5():
         global p
         if p<=1:
                 xy[5]=1
                 x5.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[5]=2
                 x5.config(state=tk.DISABLED,bg = 'black')
def xy6():
         global p
         if p<=1:
                 xy[6]=1
                 x6.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[6]=2
                 x6.config(state=tk.DISABLED,bg = 'black')
def xy7():
         global p
         if p<=1:
                 xy[7]=1
                 x7.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[7]=2
                 x7.config(state=tk.DISABLED,bg = 'black')
def xy8():
         global p
         if p<=1:
                 xy[8]=1
                 x8.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[8]=2
                 x8.config(state=tk.DISABLED,bg = 'black')
def xy9():
         global p
         if p<=1:
                 xy[9]=1
                 x9.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[9]=2
                 x9.config(state=tk.DISABLED,bg = 'black')
def xy10():
         global p
         if p<=1:
                 xy[10]=1
                 x10.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[10]=2
                 x10.config(state=tk.DISABLED,bg = 'black')
def xy11():
         global p
         if p<=1:
                 xy[11]=1
                 x11.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[11]=2
                 x11.config(state=tk.DISABLED,bg = 'black')
def xy12():
         global p
         if p<=1:
                 xy[12]=1
                 x12.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[12]=2
                 x12.config(state=tk.DISABLED,bg = 'black')
def xy13():
         global p
         if p<=1:
                 xy[13]=1
                 x13.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[13]=2
                 x13.config(state=tk.DISABLED,bg = 'black')
def xy14():
         global p
         if p<=1:
                 xy[14]=1
                 x14.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[14]=2
                 x14.config(state=tk.DISABLED,bg = 'black')
def xy15():
         global p
         if p<=1:
                 xy[15]=1
                 x15.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[15]=2
                 x15.config(state=tk.DISABLED,bg = 'black')
def xy16():
         global p
         if p<=1:
                 xy[16]=1
                 x16.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[16]=2
                 x16.config(state=tk.DISABLED,bg = 'black')
def xy17():
         global p
         if p<=1:
                 xy[17]=1
                 x17.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[17]=2
                 x17.config(state=tk.DISABLED,bg = 'black')
def xy18():
         global p
         if p<=1:
                 xy[18]=1
                 x18.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[18]=2
                 x18.config(state=tk.DISABLED,bg = 'black')
def xy19():
         global p
         if p<=1:
                 xy[19]=1
                 x19.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[19]=2
                 x19.config(state=tk.DISABLED,bg = 'black')
def xy20():
         global p
         if p<=1:
                 xy[20]=1
                 x20.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[20]=2
                 x20.config(state=tk.DISABLED,bg = 'black')
def xy21():
         global p
         if p<=1:
                 xy[21]=1
                 x21.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[21]=2
                 x21.config(state=tk.DISABLED,bg = 'black')
def xy22():
         global p
         if p<=1:
                 xy[22]=1
                 x22.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[22]=2
                 x22.config(state=tk.DISABLED,bg = 'black')
def xy23():
         global p
         if p<=1:
                 xy[23]=1
                 x23.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[23]=2
                 x23.config(state=tk.DISABLED,bg = 'black')
def xy24():
         global p
         if p<=1:
                 xy[24]=1
                 x24.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[24]=2
                 x24.config(state=tk.DISABLED,bg = 'black')
def xy25():
         global p
         if p<=1:
                 xy[25]=1
                 x25.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[25]=2
                 x25.config(state=tk.DISABLED,bg = 'black')
def xy26():
         global p
         if p<=1:
                 xy[26]=1
                 x26.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[26]=2
                 x26.config(state=tk.DISABLED,bg = 'black')
def xy27():
         global p
         if p<=1:
                 xy[27]=1
                 x27.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[27]=2
                 x27.config(state=tk.DISABLED,bg = 'black')
def xy28():
         global p
         if p<=1:
                 xy[28]=1
                 x28.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[28]=2
                 x28.config(state=tk.DISABLED,bg = 'black')
def xy29():
         global p
         if p<=1:
                 xy[29]=1
                 x29.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[29]=2
                 x29.config(state=tk.DISABLED,bg = 'black')
def xy30():
         global p
         if p<=1:
                 xy[30]=1
                 x30.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[30]=2
                 x30.config(state=tk.DISABLED,bg = 'black')
def xy31():
         global p
         if p<=1:
                 xy[31]=1
                 x31.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[31]=2
                 x31.config(state=tk.DISABLED,bg = 'black')
def xy32():
         global p
         if p<=1:
                 xy[32]=1
                 x32.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[32]=2
                 x32.config(state=tk.DISABLED,bg = 'black')
def xy33():
         global p
         if p<=1:
                 xy[33]=1
                 x33.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[33]=2
                 x33.config(state=tk.DISABLED,bg = 'black')
def xy34():
         global p
         if p<=1:
                 xy[34]=1
                 x34.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[34]=2
                 x34.config(state=tk.DISABLED,bg = 'black')
def xy35():
         global p
         if p<=1:
                 xy[35]=1
                 x35.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[35]=2
                 x35.config(state=tk.DISABLED,bg = 'black')
def xy36():
         global p
         if p<=1:
                 xy[36]=1
                 x36.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[36]=2
                 x36.config(state=tk.DISABLED,bg = 'black')
def xy37():
         global p
         if p<=1:
                 xy[37]=1
                 x37.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[37]=2
                 x37.config(state=tk.DISABLED,bg = 'black')
def xy38():
         global p
         if p<=1:
                 xy[38]=1
                 x38.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[38]=2
                 x38.config(state=tk.DISABLED,bg = 'black')
def xy39():
         global p
         if p<=1:
                 xy[39]=1
                 x39.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[39]=2
                 x39.config(state=tk.DISABLED,bg = 'black')
def xy40():
         global p
         if p<=1:
                 xy[40]=1
                 x40.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[40]=2
                 x40.config(state=tk.DISABLED,bg = 'black')
def xy41():
         global p
         if p<=1:
                 xy[41]=1
                 x41.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[41]=2
                 x41.config(state=tk.DISABLED,bg = 'black')
def xy42():
         global p
         if p<=1:
                 xy[42]=1
                 x42.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[42]=2
                 x42.config(state=tk.DISABLED,bg = 'black')
def xy43():
         global p
         if p<=1:
                 xy[43]=1
                 x43.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[43]=2
                 x43.config(state=tk.DISABLED,bg = 'black')
def xy44():
         global p
         if p<=1:
                 xy[44]=1
                 x44.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[44]=2
                 x44.config(state=tk.DISABLED,bg = 'black')
def xy45():
         global p
         if p<=1:
                 xy[45]=1
                 x45.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[45]=2
                 x45.config(state=tk.DISABLED,bg = 'black')
def xy46():
         global p
         if p<=1:
                 xy[46]=1
                 x46.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[46]=2
                 x46.config(state=tk.DISABLED,bg = 'black')
def xy47():
         global p
         if p<=1:
                 xy[47]=1
                 x47.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[47]=2
                 x47.config(state=tk.DISABLED,bg = 'black')
def xy48():
         global p
         if p<=1:
                 xy[48]=1
                 x48.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[48]=2
                 x48.config(state=tk.DISABLED,bg = 'black')
def xy49():
         global p
         if p<=1:
                 xy[49]=1
                 x49.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[49]=2
                 x49.config(state=tk.DISABLED,bg = 'black')
def xy50():
         global p
         if p<=1:
                 xy[50]=1
                 x50.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[50]=2
                 x50.config(state=tk.DISABLED,bg = 'black')
def xy51():
         global p
         if p<=1:
                 xy[51]=1
                 x51.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[51]=2
                 x51.config(state=tk.DISABLED,bg = 'black')
def xy52():
         global p
         if p<=1:
                 xy[52]=1
                 x52.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[52]=2
                 x52.config(state=tk.DISABLED,bg = 'black')
def xy53():
         global p
         if p<=1:
                 xy[53]=1
                 x53.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[53]=2
                 x53.config(state=tk.DISABLED,bg = 'black')
def xy54():
         global p
         if p<=1:
                 xy[54]=1
                 x54.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[54]=2
                 x54.config(state=tk.DISABLED,bg = 'black')
def xy55():
         global p
         if p<=1:
                 xy[55]=1
                 x55.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[55]=2
                 x55.config(state=tk.DISABLED,bg = 'black')
def xy56():
         global p
         if p<=1:
                 xy[56]=1
                 x56.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[56]=2
                 x56.config(state=tk.DISABLED,bg = 'black')
def xy57():
         global p
         if p<=1:
                 xy[57]=1
                 x57.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[57]=2
                 x57.config(state=tk.DISABLED,bg = 'black')
def xy58():
         global p
         if p<=1:
                 xy[58]=1
                 x58.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[58]=2
                 x58.config(state=tk.DISABLED,bg = 'black')
def xy59():
         global p
         if p<=1:
                 xy[59]=1
                 x59.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[59]=2
                 x59.config(state=tk.DISABLED,bg = 'black')
def xy60():
         global p
         if p<=1:
                 xy[60]=1
                 x60.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[60]=2
                 x60.config(state=tk.DISABLED,bg = 'black')
def xy61():
         global p
         if p<=1:
                 xy[61]=1
                 x61.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[61]=2
                 x61.config(state=tk.DISABLED,bg = 'black')
def xy62():
         global p
         if p<=1:
                 xy[62]=1
                 x62.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[62]=2
                 x62.config(state=tk.DISABLED,bg = 'black')
def xy63():
         global p
         if p<=1:
                 xy[63]=1
                 x63.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[63]=2
                 x63.config(state=tk.DISABLED,bg = 'black')
def xy64():
         global p
         if p<=1:
                 xy[64]=1
                 x64.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[64]=2
                 x64.config(state=tk.DISABLED,bg = 'black')
def xy65():
         global p
         if p<=1:
                 xy[65]=1
                 x65.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[65]=2
                 x65.config(state=tk.DISABLED,bg = 'black')
def xy66():
         global p
         if p<=1:
                 xy[66]=1
                 x66.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[66]=2
                 x66.config(state=tk.DISABLED,bg = 'black')
def xy67():
         global p
         if p<=1:
                 xy[67]=1
                 x67.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[67]=2
                 x67.config(state=tk.DISABLED,bg = 'black')
def xy68():
         global p
         if p<=1:
                 xy[68]=1
                 x68.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[68]=2
                 x68.config(state=tk.DISABLED,bg = 'black')
def xy69():
         global p
         if p<=1:
                 xy[69]=1
                 x69.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[69]=2
                 x69.config(state=tk.DISABLED,bg = 'black')
def xy70():
         global p
         if p<=1:
                 xy[70]=1
                 x70.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[70]=2
                 x70.config(state=tk.DISABLED,bg = 'black')
def xy71():
         global p
         if p<=1:
                 xy[71]=1
                 x71.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[71]=2
                 x71.config(state=tk.DISABLED,bg = 'black')
def xy72():
         global p
         if p<=1:
                 xy[72]=1
                 x72.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[72]=2
                 x72.config(state=tk.DISABLED,bg = 'black')
def xy73():
         global p
         if p<=1:
                 xy[73]=1
                 x73.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[73]=2
                 x73.config(state=tk.DISABLED,bg = 'black')
def xy74():
         global p
         if p<=1:
                 xy[74]=1
                 x74.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[74]=2
                 x74.config(state=tk.DISABLED,bg = 'black')
def xy75():
         global p
         if p<=1:
                 xy[75]=1
                 x75.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[75]=2
                 x75.config(state=tk.DISABLED,bg = 'black')
def xy76():
         global p
         if p<=1:
                 xy[76]=1
                 x76.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[76]=2
                 x76.config(state=tk.DISABLED,bg = 'black')
def xy77():
         global p
         if p<=1:
                 xy[77]=1
                 x77.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[77]=2
                 x77.config(state=tk.DISABLED,bg = 'black')
def xy78():
         global p
         if p<=1:
                 xy[78]=1
                 x78.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[78]=2
                 x78.config(state=tk.DISABLED,bg = 'black')
def xy79():
         global p
         if p<=1:
                 xy[79]=1
                 x79.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[79]=2
                 x79.config(state=tk.DISABLED,bg = 'black')
def xy80():
         global p
         if p<=1:
                 xy[80]=1
                 x80.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[80]=2
                 x80.config(state=tk.DISABLED,bg = 'black')
def xy81():
         global p
         if p<=1:
                 xy[81]=1
                 x81.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[81]=2
                 x81.config(state=tk.DISABLED,bg = 'black')
def xy82():
         global p
         if p<=1:
                 xy[82]=1
                 x82.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[82]=2
                 x82.config(state=tk.DISABLED,bg = 'black')
def xy83():
         global p
         if p<=1:
                 xy[83]=1
                 x83.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[83]=2
                 x83.config(state=tk.DISABLED,bg = 'black')
def xy84():
         global p
         if p<=1:
                 xy[84]=1
                 x84.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[84]=2
                 x84.config(state=tk.DISABLED,bg = 'black')
def xy85():
         global p
         if p<=1:
                 xy[85]=1
                 x85.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[85]=2
                 x85.config(state=tk.DISABLED,bg = 'black')
def xy86():
         global p
         if p<=1:
                 xy[86]=1
                 x86.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[86]=2
                 x86.config(state=tk.DISABLED,bg = 'black')
def xy87():
         global p
         if p<=1:
                 xy[87]=1
                 x87.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[87]=2
                 x87.config(state=tk.DISABLED,bg = 'black')
def xy88():
         global p
         if p<=1:
                 xy[88]=1
                 x88.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[88]=2
                 x88.config(state=tk.DISABLED,bg = 'black')
def xy89():
         global p
         if p<=1:
                 xy[89]=1
                 x89.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[89]=2
                 x89.config(state=tk.DISABLED,bg = 'black')
def xy90():
         global p
         if p<=1:
                 xy[90]=1
                 x90.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[90]=2
                 x90.config(state=tk.DISABLED,bg = 'black')
def xy91():
         global p
         if p<=1:
                 xy[91]=1
                 x91.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[91]=2
                 x91.config(state=tk.DISABLED,bg = 'black')
def xy92():
         global p
         if p<=1:
                 xy[92]=1
                 x92.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[92]=2
                 x92.config(state=tk.DISABLED,bg = 'black')
def xy93():
         global p
         if p<=1:
                 xy[93]=1
                 x93.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[93]=2
                 x93.config(state=tk.DISABLED,bg = 'black')
def xy94():
         global p
         if p<=1:
                 xy[94]=1
                 x94.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[94]=2
                 x94.config(state=tk.DISABLED,bg = 'black')
def xy95():
         global p
         if p<=1:
                 xy[95]=1
                 x95.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[95]=2
                 x95.config(state=tk.DISABLED,bg = 'black')
def xy96():
         global p
         if p<=1:
                 xy[96]=1
                 x96.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[96]=2
                 x96.config(state=tk.DISABLED,bg = 'black')
def xy97():
         global p
         if p<=1:
                 xy[97]=1
                 x97.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[97]=2
                 x97.config(state=tk.DISABLED,bg = 'black')
def xy98():
         global p
         if p<=1:
                 xy[98]=1
                 x98.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[98]=2
                 x98.config(state=tk.DISABLED,bg = 'black')
def xy99():
         global p
         if p<=1:
                 xy[99]=1
                 x99.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[99]=2
                 x99.config(state=tk.DISABLED,bg = 'black')
def xy100():
         global p
         if p<=1:
                 xy[100]=1
                 x100.config(state=tk.DISABLED,bg = '#ffffff')
         elif p>=2 and p<=4:
                 xy[100]=2
                 x100.config(state=tk.DISABLED,bg = 'black')

def winn():
    global p
    global m
    if p<=1:
            frame1['bg'] = 'black'
    elif p>=2:
            frame1['bg'] = '#ffffff'
    if m==0:
        m=2
    p = p+m
    if p==4:
        p = 0
    ww1.config(state=tk.DISABLED)
    ww2.config(state=tk.DISABLED)
    w=0
    for w0 in range(0,96+1):
        for w2 in range(1,2+1):
            if xy[w0]==w2:
                w4 = 0
                w5 = 0
                w6 = 0
                w7 = 0
                for w3 in range(0,4+1):
                    ww = w0%10
                    if (ww==0):ww = 10
                    if xy[w0+w3]==w2 and ww<7:
                        w4 = w4+1
                        if w4==5:
                            w = w2
                    if w0<61 and xy[w0+(10*w3)]==w2:
                        w5 = w5+1
                        if w5==5:
                            w = w2
                    if w0<57 and xy[w0+(10*w3)+w3]==w2 and ww<7:
                        w6 = w6+1
                        if w6==5:
                            w = w2
                    if w0<61 and xy[w0+(w3*10)-w3]==w2 and ww>4:
                        w7 = w7+1
                        if w7==5:
                            w = w2
    p=p
    if w==1:
        from tkinter import messagebox
        messagebox.showinfo("win", "恭喜白棋獲勝")
        p=5
    if w==2:
        from tkinter import messagebox
        messagebox.showinfo("win", "恭喜黑棋獲勝")
        p=5
    return p


def m1():
    global m
    m = 2
    from tkinter import messagebox
    messagebox.showinfo("模式1", "一次放1個棋子")
    return m
def m2():
    global m
    m = 1
    from tkinter import messagebox
    messagebox.showinfo("模式2", "一次可以放2個棋子")
    return m
def r():
        global p
        global m
        for a in range(0,100):
            xy[a]=0
        p = 0
        m = 0
        ww1.config(state=tk.NORMAL)
        ww2.config(state=tk.NORMAL)
        x1.config(state=tk.NORMAL,bg = 'grey')
        x2.config(state=tk.NORMAL,bg = 'grey')
        x3.config(state=tk.NORMAL,bg = 'grey')
        x4.config(state=tk.NORMAL,bg = 'grey')
        x5.config(state=tk.NORMAL,bg = 'grey')
        x6.config(state=tk.NORMAL,bg = 'grey')
        x7.config(state=tk.NORMAL,bg = 'grey')
        x8.config(state=tk.NORMAL,bg = 'grey')
        x9.config(state=tk.NORMAL,bg = 'grey')
        x10.config(state=tk.NORMAL,bg = 'grey')
        x11.config(state=tk.NORMAL,bg = 'grey')
        x12.config(state=tk.NORMAL,bg = 'grey')
        x13.config(state=tk.NORMAL,bg = 'grey')
        x14.config(state=tk.NORMAL,bg = 'grey')
        x15.config(state=tk.NORMAL,bg = 'grey')
        x16.config(state=tk.NORMAL,bg = 'grey')
        x17.config(state=tk.NORMAL,bg = 'grey')
        x18.config(state=tk.NORMAL,bg = 'grey')
        x19.config(state=tk.NORMAL,bg = 'grey')
        x20.config(state=tk.NORMAL,bg = 'grey')
        x21.config(state=tk.NORMAL,bg = 'grey')
        x22.config(state=tk.NORMAL,bg = 'grey')
        x23.config(state=tk.NORMAL,bg = 'grey')
        x24.config(state=tk.NORMAL,bg = 'grey')
        x25.config(state=tk.NORMAL,bg = 'grey')
        x26.config(state=tk.NORMAL,bg = 'grey')
        x27.config(state=tk.NORMAL,bg = 'grey')
        x28.config(state=tk.NORMAL,bg = 'grey')
        x29.config(state=tk.NORMAL,bg = 'grey')
        x30.config(state=tk.NORMAL,bg = 'grey')
        x31.config(state=tk.NORMAL,bg = 'grey')
        x32.config(state=tk.NORMAL,bg = 'grey')
        x33.config(state=tk.NORMAL,bg = 'grey')
        x34.config(state=tk.NORMAL,bg = 'grey')
        x35.config(state=tk.NORMAL,bg = 'grey')
        x36.config(state=tk.NORMAL,bg = 'grey')
        x37.config(state=tk.NORMAL,bg = 'grey')
        x38.config(state=tk.NORMAL,bg = 'grey')
        x39.config(state=tk.NORMAL,bg = 'grey')
        x40.config(state=tk.NORMAL,bg = 'grey')
        x41.config(state=tk.NORMAL,bg = 'grey')
        x42.config(state=tk.NORMAL,bg = 'grey')
        x43.config(state=tk.NORMAL,bg = 'grey')
        x44.config(state=tk.NORMAL,bg = 'grey')
        x45.config(state=tk.NORMAL,bg = 'grey')
        x46.config(state=tk.NORMAL,bg = 'grey')
        x47.config(state=tk.NORMAL,bg = 'grey')
        x48.config(state=tk.NORMAL,bg = 'grey')
        x49.config(state=tk.NORMAL,bg = 'grey')
        x50.config(state=tk.NORMAL,bg = 'grey')
        x51.config(state=tk.NORMAL,bg = 'grey')
        x52.config(state=tk.NORMAL,bg = 'grey')
        x53.config(state=tk.NORMAL,bg = 'grey')
        x54.config(state=tk.NORMAL,bg = 'grey')
        x55.config(state=tk.NORMAL,bg = 'grey')
        x56.config(state=tk.NORMAL,bg = 'grey')
        x57.config(state=tk.NORMAL,bg = 'grey')
        x58.config(state=tk.NORMAL,bg = 'grey')
        x59.config(state=tk.NORMAL,bg = 'grey')
        x60.config(state=tk.NORMAL,bg = 'grey')
        x61.config(state=tk.NORMAL,bg = 'grey')
        x62.config(state=tk.NORMAL,bg = 'grey')
        x63.config(state=tk.NORMAL,bg = 'grey')
        x64.config(state=tk.NORMAL,bg = 'grey')
        x65.config(state=tk.NORMAL,bg = 'grey')
        x66.config(state=tk.NORMAL,bg = 'grey')
        x67.config(state=tk.NORMAL,bg = 'grey')
        x68.config(state=tk.NORMAL,bg = 'grey')
        x69.config(state=tk.NORMAL,bg = 'grey')
        x70.config(state=tk.NORMAL,bg = 'grey')
        x71.config(state=tk.NORMAL,bg = 'grey')
        x72.config(state=tk.NORMAL,bg = 'grey')
        x73.config(state=tk.NORMAL,bg = 'grey')
        x74.config(state=tk.NORMAL,bg = 'grey')
        x75.config(state=tk.NORMAL,bg = 'grey')
        x76.config(state=tk.NORMAL,bg = 'grey')
        x77.config(state=tk.NORMAL,bg = 'grey')
        x78.config(state=tk.NORMAL,bg = 'grey')
        x79.config(state=tk.NORMAL,bg = 'grey')
        x80.config(state=tk.NORMAL,bg = 'grey')
        x81.config(state=tk.NORMAL,bg = 'grey')
        x82.config(state=tk.NORMAL,bg = 'grey')
        x83.config(state=tk.NORMAL,bg = 'grey')
        x84.config(state=tk.NORMAL,bg = 'grey')
        x85.config(state=tk.NORMAL,bg = 'grey')
        x86.config(state=tk.NORMAL,bg = 'grey')
        x87.config(state=tk.NORMAL,bg = 'grey')
        x88.config(state=tk.NORMAL,bg = 'grey')
        x89.config(state=tk.NORMAL,bg = 'grey')
        x90.config(state=tk.NORMAL,bg = 'grey')
        x91.config(state=tk.NORMAL,bg = 'grey')
        x92.config(state=tk.NORMAL,bg = 'grey')
        x93.config(state=tk.NORMAL,bg = 'grey')
        x94.config(state=tk.NORMAL,bg = 'grey')
        x95.config(state=tk.NORMAL,bg = 'grey')
        x96.config(state=tk.NORMAL,bg = 'grey')
        x97.config(state=tk.NORMAL,bg = 'grey')
        x98.config(state=tk.NORMAL,bg = 'grey')
        x99.config(state=tk.NORMAL,bg = 'grey')
        x100.config(state=tk.NORMAL,bg = 'grey')
        return p
        return m
#GUI介面
import tkinter as tk
win = tk.Tk()
win.title("五子棋")
win.configure(bg='#abcdef')
frame = tk.Frame(win,bg='#000000')
frame.pack(padx=20, pady=1)
frame1 = tk.Frame(win,bg='#000000')
frame1.pack(padx=20, pady=20)
#模式1的按鈕設定，以command = m1進入函示庫
ww1 = tk.Button(frame1, text="模式1 ",command = m1)
ww1.grid(column=0,row=0,columnspan=3)
#模式2的按鈕設定，以command = m2進入函示庫
ww2 = tk.Button(frame1, text="模式2 ",command = m2)
ww2.grid(column=3,row=0,columnspan=3)
#重新按鈕設定，以command = r 進入函示庫
r = tk.Button(frame1, text=" 重新 ",command = r)
r.grid(column=6,row=0,columnspan=3)
#之後是設定每個格子的按鍵，每個都有進入一個各子的函示庫和一個判斷輸贏的程式
x1 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy1(),winn()],width=3,height=2)
x1.grid(column=0,row=1)
x2 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy2(),winn()],width=3,height=2)
x2.grid(column=1,row=1)
x3 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy3(),winn()],width=3,height=2)
x3.grid(column=2,row=1)
x4 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy4(),winn()],width=3,height=2)
x4.grid(column=3,row=1)
x5 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy5(),winn()],width=3,height=2)
x5.grid(column=4,row=1)#


x6 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy6(),winn()],width=3,height=2)
x6.grid(column=5,row=1)
x7 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy7(),winn()],width=3,height=2)
x7.grid(column=6,row=1)
x8 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy8(),winn()],width=3,height=2)
x8.grid(column=7,row=1)
x9 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy9(),winn()],width=3,height=2)
x9.grid(column=8,row=1)
x10 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy10(),winn()],width=3,height=2)
x10.grid(column=9,row=1)
x11 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy11(),winn()],width=3,height=2)
x11.grid(column=0,row=2)
x12 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy12(),winn()],width=3,height=2)
x12.grid(column=1,row=2)
x13 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy13(),winn()],width=3,height=2)
x13.grid(column=2,row=2)
x14 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy14(),winn()],width=3,height=2)
x14.grid(column=3,row=2)
x15 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy15(),winn()],width=3,height=2)
x15.grid(column=4,row=2)
x16 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy16(),winn()],width=3,height=2)
x16.grid(column=5,row=2)
x17 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy17(),winn()],width=3,height=2)
x17.grid(column=6,row=2)
x18 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy18(),winn()],width=3,height=2)
x18.grid(column=7,row=2)
x19 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy19(),winn()],width=3,height=2)
x19.grid(column=8,row=2)
x20 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy20(),winn()],width=3,height=2)
x20.grid(column=9,row=2)
x21 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy21(),winn()],width=3,height=2)
x21.grid(column=0,row=3)
x22 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy22(),winn()],width=3,height=2)
x22.grid(column=1,row=3)
x23 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy23(),winn()],width=3,height=2)
x23.grid(column=2,row=3)
x24 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy24(),winn()],width=3,height=2)
x24.grid(column=3,row=3)
x25 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy25(),winn()],width=3,height=2)
x25.grid(column=4,row=3)
x26 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy26(),winn()],width=3,height=2)
x26.grid(column=5,row=3)
x27 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy27(),winn()],width=3,height=2)
x27.grid(column=6,row=3)
x28 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy28(),winn()],width=3,height=2)
x28.grid(column=7,row=3)
x29 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy29(),winn()],width=3,height=2)
x29.grid(column=8,row=3)
x30 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy30(),winn()],width=3,height=2)
x30.grid(column=9,row=3)
x31 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy31(),winn()],width=3,height=2)
x31.grid(column=0,row=4)
x32 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy32(),winn()],width=3,height=2)
x32.grid(column=1,row=4)
x33 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy33(),winn()],width=3,height=2)
x33.grid(column=2,row=4)
x34 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy34(),winn()],width=3,height=2)
x34.grid(column=3,row=4)
x35 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy35(),winn()],width=3,height=2)
x35.grid(column=4,row=4)
x36 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy36(),winn()],width=3,height=2)
x36.grid(column=5,row=4)
x37 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy37(),winn()],width=3,height=2)
x37.grid(column=6,row=4)
x38 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy38(),winn()],width=3,height=2)
x38.grid(column=7,row=4)
x39 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy39(),winn()],width=3,height=2)
x39.grid(column=8,row=4)
x40 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy40(),winn()],width=3,height=2)
x40.grid(column=9,row=4)
x41 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy41(),winn()],width=3,height=2)
x41.grid(column=0,row=5)
x42 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy42(),winn()],width=3,height=2)
x42.grid(column=1,row=5)
x43 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy43(),winn()],width=3,height=2)
x43.grid(column=2,row=5)
x44 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy44(),winn()],width=3,height=2)
x44.grid(column=3,row=5)
x45 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy45(),winn()],width=3,height=2)
x45.grid(column=4,row=5)
x46 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy46(),winn()],width=3,height=2)
x46.grid(column=5,row=5)
x47 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy47(),winn()],width=3,height=2)
x47.grid(column=6,row=5)
x48 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy48(),winn()],width=3,height=2)
x48.grid(column=7,row=5)
x49 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy49(),winn()],width=3,height=2)
x49.grid(column=8,row=5)
x50 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy50(),winn()],width=3,height=2)
x50.grid(column=9,row=5)
x51 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy51(),winn()],width=3,height=2)
x51.grid(column=0,row=6)
x52 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy52(),winn()],width=3,height=2)
x52.grid(column=1,row=6)
x53 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy53(),winn()],width=3,height=2)
x53.grid(column=2,row=6)
x54 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy54(),winn()],width=3,height=2)
x54.grid(column=3,row=6)
x55 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy55(),winn()],width=3,height=2)
x55.grid(column=4,row=6)
x56 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy56(),winn()],width=3,height=2)
x56.grid(column=5,row=6)
x57 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy57(),winn()],width=3,height=2)
x57.grid(column=6,row=6)
x58 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy58(),winn()],width=3,height=2)
x58.grid(column=7,row=6)
x59 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy59(),winn()],width=3,height=2)
x59.grid(column=8,row=6)
x60 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy60(),winn()],width=3,height=2)
x60.grid(column=9,row=6)
x61 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy61(),winn()],width=3,height=2)
x61.grid(column=0,row=7)
x62 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy62(),winn()],width=3,height=2)
x62.grid(column=1,row=7)
x63 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy63(),winn()],width=3,height=2)
x63.grid(column=2,row=7)
x64 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy64(),winn()],width=3,height=2)
x64.grid(column=3,row=7)
x65 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy65(),winn()],width=3,height=2)
x65.grid(column=4,row=7)
x66 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy66(),winn()],width=3,height=2)
x66.grid(column=5,row=7)
x67 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy67(),winn()],width=3,height=2)
x67.grid(column=6,row=7)
x68 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy68(),winn()],width=3,height=2)
x68.grid(column=7,row=7)
x69 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy69(),winn()],width=3,height=2)
x69.grid(column=8,row=7)
x70 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy70(),winn()],width=3,height=2)
x70.grid(column=9,row=7)
x71 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy71(),winn()],width=3,height=2)
x71.grid(column=0,row=8)
x72 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy72(),winn()],width=3,height=2)
x72.grid(column=1,row=8)
x73 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy73(),winn()],width=3,height=2)
x73.grid(column=2,row=8)
x74 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy74(),winn()],width=3,height=2)
x74.grid(column=3,row=8)
x75 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy75(),winn()],width=3,height=2)
x75.grid(column=4,row=8)
x76 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy76(),winn()],width=3,height=2)
x76.grid(column=5,row=8)
x77 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy77(),winn()],width=3,height=2)
x77.grid(column=6,row=8)
x78 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy78(),winn()],width=3,height=2)
x78.grid(column=7,row=8)
x79 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy79(),winn()],width=3,height=2)
x79.grid(column=8,row=8)
x80 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy80(),winn()],width=3,height=2)
x80.grid(column=9,row=8)
x81 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy81(),winn()],width=3,height=2)
x81.grid(column=0,row=9)
x82 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy82(),winn()],width=3,height=2)
x82.grid(column=1,row=9)
x83 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy83(),winn()],width=3,height=2)
x83.grid(column=2,row=9)
x84 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy84(),winn()],width=3,height=2)
x84.grid(column=3,row=9)
x85 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy85(),winn()],width=3,height=2)
x85.grid(column=4,row=9)
x86 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy86(),winn()],width=3,height=2)
x86.grid(column=5,row=9)
x87 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy87(),winn()],width=3,height=2)
x87.grid(column=6,row=9)
x88 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy88(),winn()],width=3,height=2)
x88.grid(column=7,row=9)
x89 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy89(),winn()],width=3,height=2)
x89.grid(column=8,row=9)
x90 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy90(),winn()],width=3,height=2)
x90.grid(column=9,row=9)
x91 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy91(),winn()],width=3,height=2)
x91.grid(column=0,row=10)
x92 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy92(),winn()],width=3,height=2)
x92.grid(column=1,row=10)
x93 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy93(),winn()],width=3,height=2)
x93.grid(column=2,row=10)
x94 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy94(),winn()],width=3,height=2)
x94.grid(column=3,row=10)
x95 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy95(),winn()],width=3,height=2)
x95.grid(column=4,row=10)
x96 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy96(),winn()],width=3,height=2)
x96.grid(column=5,row=10)
x97 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy97(),winn()],width=3,height=2)
x97.grid(column=6,row=10)
x98 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy98(),winn()],width=3,height=2)
x98.grid(column=7,row=10)
x99 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy99(),winn()],width=3,height=2)
x99.grid(column=8,row=10)
x100 = tk.Button(frame1,text=" ",bg='grey',command = lambda:[xy100(),winn()],width=3,height=2)
x100.grid(column=9,row=10)

win.mainloop()


