import csv
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import curve_fit
import pandas as pd
from sklearn.metrics import r2_score
import math

def slope(x1,x2,y1,y2):
    return(y2-y1)/(x2-x1)

def func(x, a,b,c,n):
    return c+a*(x+np.abs(b))**(n)

def lin(x,a,b):
    return a*x+b

def poly(x,a,b,c,d):
    return a*x**3+b*x**2+c*x**1+d

def curvefitpoly(data):
    strain = []
    stress = []
    for i in data:
        strain.append(i[0])
        stress.append(i[1])
    popt, pcov = curve_fit(poly, strain,stress,p0=[4500,0.001,5,0.1],maxfev=5000)
    stressnew=[]
    fitdata=[]
    for i in strain:
        stressnew.append(poly(i,popt[0],popt[1],popt[2],popt[3]))
        fitdata.append([i,poly(i,popt[0],popt[1],popt[2],popt[3])])
    
    return strain,stressnew


def curvefitlinear(data):
    strain = []
    stress = []
    for i in data:
        strain.append(i[0])
        stress.append(i[1])
    popt, pcov = curve_fit(lin, strain,stress,p0=[3,5],maxfev=50000)
    stressnew=[]
    for i in strain:
        stressnew.append(lin(i,popt[0],popt[1]))
    return strain,stressnew,popt

def curvefitpower(data):
    strain = []
    stress = []
    for i in data:
        strain.append(i[0])
        stress.append(i[1])
    try:
        popt, pcov = curve_fit(func, strain,stress,p0=[4500,0.001,5,0.1],maxfev=50000)
    except:
        popt, pcov = curve_fit(func, strain,stress,p0=[4500,0.001,5,0.1],bounds=((-1e15, -1e15, -1e15, -1e15), (1e15, 1e15, 1e15, 1e15)))
    stressnew=[]
    for i in strain:
        stressnew.append(func(i,popt[0],popt[1],popt[2],popt[3]))
    return strain,stressnew

def Modulus(strain,stress):

    slopes = []
    for i in range(len(strain)-1):

        slopes.append(slope(strain[i],strain[i+1],stress[i],stress[i+1]))
    return max(slopes)

filename = str(input("Enter the file name: "))

#filename = 'Al5086_Tensile_Specimen_3_R0'

#filename = 'AL_5086_Shear_Specimen_5_R0 Stripped'

#filename = 'AL_5086_Plane_Strain_Tension_Specimen_1_R0'

#filename = 'Al5086_Tensile_Specimen_3_R0 Stripped'


df = pd.read_csv(filename+'.csv', na_values=[''],skiprows=1)

print(df)  

'''with open(filename,mode='r+',newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    print(type(reader))
    data=[]
    for row in reader:
        temp = float(row['Eng Strain'])
        if temp<=0:
            temp = 0.000001
        data.append([temp,abs(float(row['Eng Stress(MPa)']))])
    data=np.array(data)'''

#print(data)

if 'Eng Strain' not in df.columns or 'Eng Stress(MPa)' not in df.columns:

    print('No Stress strain data present')

    stype = input('Please enter the stress type: (Tension:t, Compression: c, PST: p, Shear: s): ')

    Htr = int(input('Is the specimen HTr? Load division by: (1/4): '))

    csc= float(input('Enter the cross section width (mm): '))
    th = float(input('Enter the thickness (mm): '))

    
    Load = [abs(i*10000/(Htr)) for i in df['Dev1/ai0'].to_list()]

    Disp = [abs(i) for i in df['V [mm]'].to_list()]

    Engstress = [i/(csc*th) for i in Load]

    if stype =='t' or stype=='c' or stype =='p':
        
        Truestrain = [abs(i) for i in df['eyy [1] - Hencky'].to_list()]

    if stype =='s':
        
        Truestrain = [abs(i) for i in df['exy [1] - Hencky'].to_list()]

    Engstrain = [math.exp(i)-1 for i in Truestrain]

    Truestress = []

    for i in range(len(Engstrain)):
        Truestress.append(Engstress[i]*(1+Engstrain[i]))

    df2 = pd.DataFrame({
        'Disp (mm)': Disp,
        'Load (N)':Load,
        'Eng Strain':Engstrain,
        'Eng Stress(MPa)':Engstress,
        'True Strain (mm/mm)':Truestrain,
        'True Stress (MPa)':Truestress
        })

    df = pd.concat([df,df2],axis=1)

    

print(df)     
    
    

e1 = df['Eng Strain'].to_list()
s1 = df['Eng Stress(MPa)'].to_list()

data = []
for i in range(len(e1)):
    if e1[i]==0:
        e1[i]= 0.0000001
    data.append([e1[i],s1[i]])  

trace1 = go.Scatter(x=e1,y=s1,mode='markers',name = 'Experimental Result')

#Elastic Region

r2score=[]
percents = []

    
for i in range(1000):
    percent=(i+1)/1000

    try:
        splitdata = data[:int(len(data)*percent)]
        strainnew,stressnew,popt=curvefitlinear(splitdata)
        s1split =[]
        for i in splitdata:
            s1split.append(i[1])
        r2 = r2_score(s1split, stressnew)

        #print("Elastic Fit Score: ", r2," at percent ",percent*100)
        r2score.append(r2)
        percents.append(percent)
    except:
        print('Pushing forward')

for i in range(r2score.count(1.0)):
    popitem=r2score.index(max(r2score))
    r2score.pop(popitem)
    percents.pop(popitem)
percent=percents[r2score.index(max(r2score))]

r2score=[]
percents = []

    
for i in range(int(percent*1000)):
    percenti=(i)/1000

    try:
        splitdata = data[int(len(data)*percenti):int(len(data)*percent)]
        strainnew,stressnew,popt=curvefitlinear(splitdata)
        s1split =[]
        for i in splitdata:
            s1split.append(i[1])
        r2 = r2_score(s1split, stressnew)

        #print("Elastic Fit Score: ", r2," at percent ",percent*100)
        r2score.append(r2)
        percents.append(percenti)
    except:
        print('Pushing forward')



for i in range(r2score.count(1.0)):
    popitem=r2score.index(max(r2score))
    r2score.pop(popitem)
    percents.pop(popitem)
percenti=percents[r2score.index(max(r2score))]

    
splitdata = data[int(len(data)*(percenti)):int(len(data)*(percent))]
strainnew,stressnew,popt=curvefitlinear(splitdata)
s1split =[]
for i in splitdata:
    s1split.append(i[1])
r2 = r2_score(s1split, stressnew)

modulus=popt[0]

print('Modulus',modulus)

print("Elastic Fit Score: ", r2," from percent ",percenti*100," to ", percent*100)



#Plastic region
splitdata=data[int(len(data)*percent):int(len(data)*0.3)]

s1split =[]
for i in splitdata:
    s1split.append(i[1])

strainfit,stressfit=curvefitpoly(splitdata)
r21 = r2_score(s1split, stressfit)

offset = [popt[0]*(i-0.002)+popt[1] for i in strainfit]

r = []
for i in range(len(strainfit)):
    r.append((offset[i]-stressfit[i])**2)


yieldpoint=[(strainfit[r.index(min(r))]+strainfit[r.index(min(r))+1])/2,(stressfit[r.index(min(r))]+stressfit[r.index(min(r))+1])/2]
print('Yield point',float(yieldpoint[0]),float(yieldpoint[1]))

print("Polynomial Fit Score: ", r21)


#UTS

splitdata=data[int(len(data)*percent):]

s1split =[]
for i in splitdata:
    s1split.append(i[1])

strainult,stressult=curvefitpoly(splitdata)
r22 = r2_score(s1split, stressult)





UTS=[strainult[stressult.index(max(stressult))],max(stressult)]
print('UTS',float(UTS[0]),float(UTS[1]))

print("Polynomial Fit Score: ", r22)


trace5 = go.Scatter(x=[float(yieldpoint[0])],y=[float(yieldpoint[1])],mode = 'markers',name = 'Yield Point')
trace3 = go.Scatter(x=[(-popt[1]/popt[0])+0.002,yieldpoint[0]],y=[0,popt[0]*(yieldpoint[0]-0.002)+popt[1]],mode = 'lines',name = '0.2% Offset')
trace4 = go.Scatter(x=strainfit,y=stressfit,mode = 'lines',name = 'Yield Curve Fit')
trace2 = go.Scatter(x=strainnew,y=stressnew,mode = 'lines',name = 'Elastic Curve Fit')
trace6 = go.Scatter(x=[UTS[0]],y=[UTS[1]],mode = 'markers',name = 'UTS Point')


lay1 = go.Layout(
      title =dict(text = 'Engineering Stress vs Strain',
                    font=dict(
                        size=24,
                    ),),
      title_x = 0.5,
      xaxis = dict(title=dict(text = "Engineering Strain",font = dict(size = 20)),showspikes=True,showline=True, linewidth=2, linecolor='black'),
      yaxis = dict(title=dict(text = "Engineering Stress (MPa)",font = dict(size = 20)),showspikes=True,showline=True, linewidth=2, linecolor='black'),
      template = 'plotly_white',
      hovermode = 'closest',
      
    )


curves = [trace1,trace2,trace3,trace4,trace5,trace6]

fig=go.Figure(data = curves,layout = lay1)

config = dict({'displayModeBar': True,'scrollZoom': True,'toImageButtonOptions': {
              'format': 'png', # one of png, svg, jpeg, webp
              'filename': 'Engineering Stress vs Strain Plot',}})
fig.show(config=config)

Load = df['Load (N)'].to_list()
Disp = df['Disp (mm)'].to_list()


Trace1 = go.Scatter(x=Disp,y=Load,mode='markers',name = 'Experimental Result')

lay2 = go.Layout(
      title =dict(text = 'Load vs Displacement',
                    font=dict(
                        size=24,
                    ),),
      title_x = 0.5,
      xaxis = dict(title=dict(text = "Displacement (mm)",font = dict(size = 20)),showspikes=True,showline=True, linewidth=2, linecolor='black'),
      yaxis = dict(title=dict(text = "Load (N)",font = dict(size = 20)),showspikes=True,showline=True, linewidth=2, linecolor='black'),
      template = 'plotly_white',
      hovermode = 'closest',
      
    )


curves = [Trace1]

fig2=go.Figure(data = curves,layout = lay2)

config2 = dict({'displayModeBar': True,'scrollZoom': True,'toImageButtonOptions': {
              'format': 'png', # one of png, svg, jpeg, webp
              'filename': 'Load vs Displacement Plot',}})
fig2.show(config=config2)


flag=input("Data looks good? Ready to write into csv? (y,n)")

if flag == 'y' or flag == 'Y':
    samplelist = ['' for i in range(len(df['Eng Strain']))]
    samplelist[0]=yieldpoint[1]
    samplelist[1]=r21
    df['2% Offset Yield Strength (MPa)']= samplelist
    samplelist[0]=yieldpoint[0]
    samplelist[1]=r21
    df['Strain @ yield']=samplelist
    samplelist[0]=modulus/1000
    samplelist[1]=r2
    df['Youngs Modulus (GPa)']=samplelist
    samplelist[0]=UTS[1]
    samplelist[1]=r22
    df['Ultimate Strength (MPa)']=samplelist

    df.to_csv(filename+' Analysis.csv')
    print('CSV File created')

flagplot=input("Save the html of plots: (y,n)")

if flagplot == 'y' or flagplot == 'Y':

    fig.write_html(filename+" Engineering Stress Strain.html", config = config, auto_open=False,full_html = False,include_plotlyjs = 'cdn')
    fig2.write_html(filename+" Load Displacement.html", config = config2, auto_open=False,full_html = False,include_plotlyjs = 'cdn')

    print('HTML Plot File created')

