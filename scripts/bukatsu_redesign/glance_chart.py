import html,datetime
E=lambda x:html.escape(str(x),quote=True)
def annotated_graph(name, rounds, j, mobile=False):
 first_date=datetime.date.fromisoformat(rounds[0]['d']);last_date=datetime.date.fromisoformat(rounds[-1]['d'])
 w=360 if mobile else 720;left=42;right=222 if mobile else 510;label=242 if mobile else 546;top=45;bottom=175
 dates=[datetime.date.fromisoformat(r['d']).toordinal() for r in rounds]
 pts=[(left+(right-left)*(dt-dates[0])/max(1,dates[-1]-dates[0]),bottom-(bottom-top)*r['v'][j]/50) for dt,r in zip(dates,rounds)]
 first,last=rounds[0],rounds[-1];x0,y0=pts[0];xe,ye=pts[-1];ly=max(62,min(130,ye))
 cls='glance-chart-mobile' if mobile else 'glance-chart-desktop'
 out=f'<svg class="{cls}" viewBox="0 0 {w} 205" role="img" aria-label="{E(name)}。{first_date.isoformat()} {first["v"][j]}%、{first["c"][j]}件。{last_date.isoformat()} {last["v"][j]}%、{last["c"][j]}件。{len(rounds)}回の収集。">'
 maximum=max(50,((int(max(r["v"][j] for r in rounds))+24)//25)*25)
 pts=[(x,bottom-(bottom-top)*r["v"][j]/maximum) for (x,_),r in zip(pts,rounds)]
 x0,y0=pts[0];xe,ye=pts[-1];ly=max(62,min(130,ye))
 for tick in [0,maximum/2,maximum]:
  y=bottom-(bottom-top)*tick/maximum
  out+=f'<line x1="{left}" x2="{right}" y1="{y}" y2="{y}" stroke="#d9e4ef"/><text class="gc-axis" x="{left-7}" y="{y+4}" text-anchor="end">{tick:g}%</text>'
 out+='<polyline fill="none" stroke="currentColor" stroke-width="2.5" points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+'"/>'
 for n,((x,y),r) in enumerate(zip(pts,rounds)):
  out+=f'<circle cx="{x}" cy="{y}" r="{5 if n in (0,len(pts)-1) else 2.8}" fill="currentColor" stroke="white" stroke-width="1.5"><title>{r["d"]}：{r["v"][j]}%（{r["c"][j]}件）</title></circle>'
 out+=f'<text class="gc-first" x="{left}" y="{y0-19}">{first["v"][j]}%<tspan class="gc-count" dx="5">{first["c"][j]}件</tspan></text>'
 out+=f'<path d="M{xe+7} {ye} L{label-7} {ly}" fill="none" stroke="#9caebe" stroke-dasharray="4 3"/><text class="gc-latest" x="{label}" y="{ly}">{last["v"][j]}%</text><text class="gc-count" x="{label}" y="{ly+21}">{last["c"][j]}件</text>'
 chunks=[name[k:k+7] for k in range(0,len(name),7)]
 for n,line in enumerate(chunks):out+=f'<text class="gc-name" x="{label}" y="{ly+42+n*16}">{E(line)}</text>'
 out+=f'<text class="gc-axis" x="{left}" y="199">{first_date.month}/{first_date.day}</text><text class="gc-axis" x="{right}" y="199" text-anchor="end">{last_date.month}/{last_date.day}</text></svg>'
 return out
