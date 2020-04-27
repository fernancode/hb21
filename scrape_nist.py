#create a p-v diagram for nitrous so when we pull temp and pressure data we can locate our state.
#will be webscraping NIST data, and leaving this so I can pull this data for another fluid if needed (ahem... methane, lox)

from bs4 import BeautifulSoup as bs
import requests
import urllib.request
import re
import numpy as np
import matplotlib.pyplot as plt

oxygen = 'C7782447'
nitrous = 'C10024972'
fluid = oxygen


#first part - max and min temp increments
url = 'https://webbook.nist.gov/cgi/fluid.cgi?ID='+fluid+'&TUnit=K&PUnit=bar&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=uPa*s&STUnit=N%2Fm&Type=SatP&RefState=DEF&Action=Page'
response = requests.get(url,headers={'user-agent':'Mozilla/5.0'})    
soup = bs(response.text, "html.parser")

raw_max_string = soup.find('input',{'name':'THigh'}).find_next('td').string
t_high= float(re.sub('[^0-9,.]','',raw_max_string))

raw_low_string = soup.find('input',{'name':'TLow'}).find_next('td').string
t_low= float(re.sub('[^0-9,.]','',raw_low_string))
t_low+=1
temps = np.linspace(t_low,t_high,10)
temps = np.around(temps,decimals=0)

#next part - get the saturation curve
url = 'https://webbook.nist.gov/cgi/fluid.cgi?Action=Load&ID='+fluid+'&Type=SatP&Digits=5&THigh='+str(t_high)+'&TLow='+str(t_low)+' &TInc=1&RefState=DEF&TUnit=K&PUnit=bar&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=uPa*s&STUnit=N%2Fm'
response = requests.get(url,headers={'user-agent':'Mozilla/5.0'})    
soup = bs(response.text, "html.parser")
rows = soup.find_all('tr')

properties = []
for content in rows[0].contents:
    properties.append(content.string)
    print(content.string)

l_temp = []
l_press = []
l_volume = []
l_enthalpy = []
v_temp = []
v_press=[]
v_volume = []
v_enthalpy = []

for row in rows[1::]:
    try:
        if row.contents[-1].text =='liquid':
            l_temp.append(float(row.contents[0].text))
            l_press.append(float(row.contents[1].text))
            l_volume.append(float(row.contents[3].text))
            l_enthalpy.append(float(row.contents[5].text))
        elif row.contents[-1].text == 'vapor':
            v_temp.append(float(row.contents[0].text))
            v_press.append(float(row.contents[1].text))
            v_volume.append(float(row.contents[3].text))
            v_enthalpy.append(float(row.contents[5].text))
        else:
            pass
    except ValueError:
        pass
    except AttributeError:
        pass

v_volume.reverse()
v_press.reverse()
volume = l_volume + v_volume
press = l_press + v_press
plt.style.use('dark_background')
fig, ax = plt.subplots()
ax.plot(volume,press,color='white')

for temp in temps:
    url = 'https://webbook.nist.gov/cgi/fluid.cgi?Action=Load&ID='+fluid+'&Type=IsoTherm&Digits=5&PLow=0&PHigh=500&PInc=1&T='+str(temp)+'&RefState=DEF&TUnit=K&PUnit=bar&DUnit=kg%2Fm3&HUnit=kJ%2Fkg&WUnit=m%2Fs&VisUnit=uPa*s&STUnit=N%2Fm'
    response = requests.get(url,headers={'user-agent':'Mozilla/5.0'})    
    soup = bs(response.text, "html.parser")
    rows = soup.find_all('tr')
    
    isotherm_p = []
    isotherm_v = []    
    for row in rows[1::]:
        try:
            isotherm_p.append(float(row.contents[1].text))
            if row.contents[3].text == 'infinite':
                isotherm_v.append(100)
            else:
                isotherm_v.append(float(row.contents[3].text))
        except ValueError:
            pass
        except AttributeError:
            pass
    ax.plot(isotherm_v,isotherm_p,label=str(temp)+'K')

plt.grid(True,linewidth='.25',linestyle='--',color='lightgray')
legend = ax.legend()
handles, labels = ax.get_legend_handles_labels()
ax.legend(reversed(handles), reversed(labels))
plt.xlim(left=.00075,right=.005)
plt.ylim(bottom=0,top=150)
plt.xlabel('m^3/kg')
plt.ylabel('bar')
plt.show()