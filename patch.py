import sys
src="week-planner-card-plus.upstream.js"
s=open(src,encoding="utf-8").read()
orig=s

# --- 1) add viewMode aliases ---
anchor1='      "timeline_week":"timelineWeek"\n    };'
assert s.count(anchor1)==1, "anchor1 not unique/found"
add1=('      "timeline_week":"timelineWeek",\n'
      '      "timelinedaybycalendar":"timelineDayByCalendar",\n'
      '      "daybycalendar":"timelineDayByCalendar",\n'
      '      "calendarcolumns":"timelineDayByCalendar",\n'
      '      "timelinecalendar":"timelineDayByCalendar",\n'
      '      "timeline_day_by_calendar":"timelineDayByCalendar"\n'
      '    };')
s=s.replace(anchor1,add1)

# --- 2) route in _renderDays ---
anchor2='    if(m==="optionD"||m==="schedule"||m==="skylight_d"){'
assert s.count(anchor2)==1, "anchor2 not unique/found"
route=('    if(m==="timelineDayByCalendar"){\n'
       '      return this._rnrRenderTimelineByCalendar?.() ?? _origRenderDays.call(this);\n'
       '    }\n')
s=s.replace(anchor2, route+anchor2)

# --- 3) append the new render function before the final catch ---
anchor3='}catch(e){console.warn("week-planner-card-plus: OptionD patch failed",e);}})();'
assert s.count(anchor3)==1, "anchor3 not unique/found"

fn=r'''
  // ---- per-calendar columns, single day (today) ----
  Card.prototype._rnrRenderTimelineByCalendar=function(){
    const days=this._days||[];
    if(!days.length) return _origRenderDays.call(this);

    // Which day is shown: today + user nav offset, clamped to the fetched range.
    // Widen the fetched range with days:/startingDayOffset: so prev/next have room.
    const todayIdx=days.findIndex(d=>{try{return this._isToday&&this._isToday(d.date)}catch(e){return false}});
    const baseIdx=todayIdx>=0?todayIdx:0;
    let idx=Math.min(days.length-1, Math.max(0, baseIdx+(this._rnrDayOffset||0)));
    this._rnrDayOffset=idx-baseIdx;
    const day=days[idx];
    const canPrev=idx>0, canNext=idx<days.length-1;
    const goDay=(delta)=>{this._rnrDayOffset=(this._rnrDayOffset||0)+delta;this.requestUpdate&&this.requestUpdate();};
    const goToday=()=>{this._rnrDayOffset=0;this.requestUpdate&&this.requestUpdate();};

    // Hourly condition indicators (right of the nav bar). Config:
    //   hourlyForecastEntity: a sensor whose `forecast` attribute is the hourly list
    //   forecastHours: [9,12,15,18,21]
    let fcHours=[9,12,15,18,21], hourlyEntity=null;
    try{
      const cfg4=(this&&(this._config||this.config))||{};
      if(Array.isArray(cfg4.forecastHours)&&cfg4.forecastHours.length)
        fcHours=cfg4.forecastHours.map(x=>parseInt(x,10)).filter(x=>Number.isFinite(x));
      hourlyEntity=cfg4.hourlyForecastEntity ?? cfg4.hourlyWeatherEntity ?? null;
    }catch(e){}
    const hourlyList=(hourlyEntity && this.hass && this.hass.states[hourlyEntity]
      && this.hass.states[hourlyEntity].attributes
      && this.hass.states[hourlyEntity].attributes.forecast) || [];
    const fcAt=(h)=>{
      for(const f of hourlyList){
        if(!f||!f.datetime) continue;
        const d=new Date(f.datetime);
        if(d.getFullYear()===day.date.year && (d.getMonth()+1)===day.date.month
           && d.getDate()===day.date.day && d.getHours()===h) return f;
      }
      return null;
    };
    const condEmoji={clear:'☀️','clear-night':'🌙',sunny:'☀️',
      partlycloudy:'⛅',cloudy:'☁️',overcast:'☁️',fog:'🌫️',
      hail:'🌨️',lightning:'⛈️','lightning-rainy':'⛈️',
      pouring:'🌧️',rainy:'🌧️',snowy:'❄️',
      'snowy-rainy':'🌨️',windy:'🌬️','windy-variant':'🌬️',
      exceptional:'⚠️'};
    const fcH12=(h)=>{const ap=h<12?'am':'pm';let hh=h%12;if(hh===0)hh=12;return hh+ap;};

    const cals=(this._calendars||[]).filter(c=>c&&c.entity&&(this._hideCalendars||[]).indexOf(c.entity)===-1);
    if(!cals.length) return _origRenderDays.call(this);
    const colCount=Math.max(1, cals.length);

    let hourHeight=96;
    try{
      const cfg=(this&&(this._config||this.config))||{};
      const cfgHH=cfg.timelineHourHeight ?? cfg.scheduleHourHeight ?? cfg.hourHeight;
      if(cfgHH!=null&&cfgHH!==""){const n=Number(cfgHH);if(Number.isFinite(n)&&n>20)hourHeight=n;}
      const cssHH=(getComputedStyle(this).getPropertyValue("--wpcp-timeline-hour-height")||"").trim();
      if(cssHH){const n2=parseFloat(cssHH);if(Number.isFinite(n2)&&n2>20)hourHeight=n2;}
    }catch(e){}
    const pxPerMin=hourHeight/60;
    const labelW=72;
    const use24=(this._rnrClockFormat==="24");

    // Visible hour window (default whole day 0..24). Config: startHour/endHour
    // (aliases dayStartHour/dayEndHour, timelineStartHour/timelineEndHour).
    let startHour=0, endHour=24;
    try{
      const cfg2=(this&&(this._config||this.config))||{};
      const shRaw=cfg2.startHour ?? cfg2.dayStartHour ?? cfg2.timelineStartHour;
      const ehRaw=cfg2.endHour ?? cfg2.dayEndHour ?? cfg2.timelineEndHour;
      if(shRaw!=null&&shRaw!==""){const n=Math.floor(Number(shRaw));if(Number.isFinite(n)&&n>=0&&n<24)startHour=n;}
      if(ehRaw!=null&&ehRaw!==""){const n=Math.floor(Number(ehRaw));if(Number.isFinite(n)&&n>startHour&&n<=24)endHour=n;}
    }catch(e){}
    const startMinWin=startHour*60, endMinWin=endHour*60;
    const hoursShown=Math.max(1, endHour-startHour);
    const winMin=Math.max(1, endMinWin-startMinWin);

    // Fill-height mode: pin the timeline to a fixed height and lay events out
    // by % of the window so nothing scrolls. Config: fillHeight: true, or
    // timelineHeight: "<css length>" (e.g. "100dvh", "calc(100dvh - 72px)").
    let wrapHeight=null;
    try{
      const cfg3=(this&&(this._config||this.config))||{};
      const thRaw=cfg3.timelineHeight ?? cfg3.calendarHeight;
      if(thRaw!=null&&thRaw!=="") wrapHeight=String(thRaw);
      else if(cfg3.fillHeight===true||cfg3.fillHeight==="true") wrapHeight="100dvh";
    }catch(e){}
    const fill=!!wrapHeight;

    const fmtHour=(h)=>{if(use24)return String(h).padStart(2,"0")+":00";const ampm=h<12?"AM":"PM";let hh=h%12;if(hh===0)hh=12;return hh+" "+ampm;};
    const fmtTime=(dt)=>{if(!dt)return "";try{const fmt=(typeof this._timeFormat==="string"&&this._timeFormat)?this._timeFormat:(use24?"HH:mm":"h:mm a");return dt.toFormat?dt.toFormat(fmt):"";}catch(e){try{return String(dt);}catch(_){return "";}}};

    const dayStart=day.date.startOf("day");
    const allEvs=this._rnrGetRenderableEventsForDay(day)||[];

    const layoutTimed=(timedRaw)=>{
      const timed=timedRaw.map((e)=>{
        const sdt=e.start||dayStart;
        const en=e.end||sdt.plus({minutes:30});
        let startMin=Math.floor(sdt.diff(dayStart,"minutes").minutes);
        let endMin=Math.ceil(en.diff(dayStart,"minutes").minutes);
        if(endMin<startMin)endMin=startMin+15;
        return {e,startMin,endMin,col:0,colCount:1};
      }).filter(it=>it.endMin>startMinWin&&it.startMin<endMinWin).map(it=>{
        it.startMin=Math.max(startMinWin,Math.min(endMinWin,it.startMin));
        it.endMin=Math.max(startMinWin,Math.min(endMinWin,it.endMin));
        if(it.endMin-it.startMin<15)it.endMin=Math.min(endMinWin,it.startMin+15);
        return it;
      }).sort((a,b)=>a.startMin-b.startMin||(b.endMin-b.startMin)-(a.endMin-a.startMin));
      let active=[],cluster=[],clusterMax=0;
      const finalize=()=>{if(!cluster.length)return;cluster.forEach(x=>x.colCount=Math.max(1,clusterMax));cluster=[];clusterMax=0;};
      timed.forEach((item)=>{
        active=active.filter(a=>a.endMin>item.startMin);
        if(active.length===0)finalize();
        const used=new Set(active.map(a=>a.col));
        let col=0;while(used.has(col))col++;
        item.col=col;active.push(item);cluster.push(item);
        clusterMax=Math.max(clusterMax,active.length,col+1);
      });
      finalize();
      return timed;
    };

    const colLayouts=cals.map((c)=>{
      const mine=allEvs.filter(ev=>Array.isArray(ev.calendars)&&ev.calendars.indexOf(c.entity)>-1);
      const fullDay=mine.filter(e=>!!e.fullDay);
      const timed=layoutTimed(mine.filter(e=>!e.fullDay));
      return {cal:c, color:(c.color||"#999"), title:(c.name||c.entity), day, fullDay, timed};
    });

    const colWExpr=(ci)=>`calc(${labelW}px + (${ci} * (100% - ${labelW}px) / ${colCount}))`;
    const baseWExpr=`calc((100% - ${labelW}px) / ${colCount})`;

    const style=W`<style>
      .timelineWrap{display:flex;flex-direction:column;gap:8px;width:100%;min-width:0;box-sizing:border-box;${fill?`height:${wrapHeight};`:''}}
      .timelineDateNav{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:2px 8px 6px 8px;}
      .timelineDateNav .navLeft{display:flex;align-items:center;gap:16px;}
      .timelineDateNav .navBtn{cursor:pointer;user-select:none;border:0;background:rgba(0,0,0,0.06);color:#333;width:40px;height:40px;border-radius:50%;font-size:1.4em;line-height:1;display:flex;align-items:center;justify-content:center;touch-action:manipulation;}
      .timelineDateNav .navBtn[disabled]{opacity:.3;cursor:default;}
      .timelineDateNav .dateLabel{cursor:pointer;text-align:center;min-width:9em;line-height:1.15;}
      .timelineDateNav .dateLabel .wd{font-weight:700;font-size:1.15em;color:#222;}
      .timelineDateNav .dateLabel .dt{font-size:0.9em;color:#666;margin-top:2px;}
      .timelineWeather{display:flex;align-items:flex-end;gap:18px;color:#333;min-height:44px;}
      .timelineWeather .wxDaily{text-align:right;line-height:1.15;}
      .timelineWeather .wxDaily .wxTemp{font-weight:700;font-size:1.25em;color:#222;}
      .timelineWeather .wxDaily .wxTemp .wxLow{font-weight:500;opacity:.6;font-size:0.8em;margin-left:4px;}
      .timelineWeather .wxDaily .wxCond{font-size:0.8em;opacity:.75;text-transform:capitalize;margin-top:2px;}
      .timelineWeather .wxHours{display:flex;align-items:flex-end;gap:12px;}
      .timelineWeather .wxHour{display:flex;flex-direction:column;align-items:center;gap:1px;min-width:34px;}
      .timelineWeather .wxHourTime{font-size:0.7em;opacity:.7;white-space:nowrap;}
      .timelineWeather .wxHourIcon{width:30px;height:30px;object-fit:contain;}
      .timelineWeather .wxHourEmoji{font-size:1.4em;line-height:1;}
      .timelineWeather .wxHourNone{font-size:1.1em;opacity:.3;line-height:1.2;}
      .timelineWeather .wxHourPop{font-size:0.68em;color:#1479b8;font-weight:600;}
      .timelineHeader{display:grid;grid-template-columns:${labelW}px repeat(${colCount},1fr);gap:8px;align-items:end;width:100%;min-width:0;}
      .timelineHeaderDay{font-weight:700;font-size:0.95em;color:#333;line-height:1.1;padding:0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
      .timelineHeaderDay .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle;background:var(--border-color,#999);}
      .timelineAllDayBar{display:grid;grid-template-columns:${labelW}px repeat(${colCount},1fr);gap:8px;align-items:start;width:100%;min-width:0;}
      .timelineAllDayLabel{padding-left:8px;font-size:0.95em;color:#666;padding-top:4px;}
      .timelineAllDayCell{padding:0 6px 2px 6px;min-height:10px;}
      .timelineAllDayPill{display:block;border-left:4px solid var(--border-color,#999);background:var(--border-color,#999);color:#fff;border-radius:999px;padding:4px 10px;margin:2px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:1em;cursor:pointer;pointer-events:auto;touch-action:manipulation;}
      .timelineBody{position:relative;overflow:${fill?'hidden':'auto'};flex:1 1 auto;min-height:0;height:100%;max-height:100%;border-radius:14px;background:rgba(255,255,255,0.35);width:100%;min-width:0;}
      .timelineGrid{position:relative;${fill?'height:100%;':`height:${hoursShown*hourHeight}px;`}width:100%;min-width:0;}
      .timelineGrid::before{content:"";position:absolute;left:${labelW}px;right:0;top:0;bottom:0;background:linear-gradient(to right, rgba(0,0,0,.06) 1px, transparent 1px);background-size:calc(100% / ${colCount}) 100%;pointer-events:none;opacity:.6;}
      .timelineHourRow{position:absolute;left:0;right:0;height:${hourHeight}px;border-top:1px solid rgba(0,0,0,0.08);pointer-events:none;z-index:1;}
      .timelineHourLabel{position:absolute;left:0;top:3px;width:${labelW}px;padding-left:8px;font-size:0.75em;color:#666;}
      .timelineEvent{box-sizing:border-box;position:absolute;min-height:14px;border-left:6px solid var(--border-color,#999);background:var(--border-color,#999);color:#fff;border-radius:10px;padding:2px 8px;overflow:hidden;box-shadow:0 2px 2px rgba(0,0,0,0.10);cursor:pointer;z-index:1;pointer-events:auto;touch-action:manipulation;line-height:1.2;}
      .timelineEvent .time{font-size:0.9em;opacity:0.9;}
      .timelineEvent .title{font-weight:600;white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
      .timelineEvent .loc{font-size:0.75em;opacity:.75;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px;}
      .timelineEvent .desc{font-size:0.78em;opacity:.85;white-space:normal;overflow:hidden;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;word-break:break-word;overflow-wrap:anywhere;margin-top:2px;}
    </style>`;

    return W`
      ${style}
      <div class="timelineWrap">
        <div class="timelineDateNav">
          <div class="navLeft">
            <button class="navBtn prev" ?disabled=${!canPrev} @click=${()=>goDay(-1)}>&#8249;</button>
            <div class="dateLabel" title="Jump to today" @click=${()=>goToday()}>
              <div class="wd">${day.date.toFormat?day.date.toFormat("cccc"):""}</div>
              <div class="dt">${day.date.toFormat?day.date.toFormat("d LLL yyyy"):""}</div>
            </div>
            <button class="navBtn next" ?disabled=${!canNext} @click=${()=>goDay(1)}>&#8250;</button>
          </div>
          <div class="timelineWeather">
            <div class="wxHours">
              ${fcHours.map(h=>{
                const f=fcAt(h);
                if(!f) return "";
                const cond=f?f.condition:null;
                // Prefer chance-of-rain (%); fall back to precipitation amount (mm).
                let popLabel="";
                if(f.precipitation_probability!=null){
                  popLabel=Math.round(f.precipitation_probability)+"%";
                } else if(f.precipitation!=null && f.precipitation!==""){
                  const mm=Number(f.precipitation);
                  if(Number.isFinite(mm)) popLabel=(Math.round(mm*10)/10)+"mm";
                }
                const icon=(cond && this._getWeatherIcon)?this._getWeatherIcon({condition:cond}):null;
                return W`<div class="wxHour">
                  <div class="wxHourTime">${fcH12(h)}</div>
                  ${cond
                    ? (icon
                        ? W`<img class="wxHourIcon" src="${icon}" alt="${cond}" title="${cond}">`
                        : W`<div class="wxHourEmoji" title="${cond}">${condEmoji[cond]||'•'}</div>`)
                    : W`<div class="wxHourNone" title="no forecast">&middot;</div>`}
                  ${popLabel ? W`<div class="wxHourPop">${popLabel}</div>` : ""}
                </div>`;
              })}
            </div>
            ${day.weather ? W`<div class="wxDaily">
              ${(day.weather.temperature!=null||day.weather.templow!=null) ? W`<div class="wxTemp">${day.weather.temperature!=null?W`${day.weather.temperature}&deg;`:""}${day.weather.templow!=null?W`<span class="wxLow">${day.weather.templow}&deg;</span>`:""}</div>` : ""}
              ${day.weather.condition ? W`<div class="wxCond">${day.weather.condition}</div>` : ""}
            </div>` : ""}
          </div>
        </div>
        <div class="timelineHeader">
          <div></div>
          ${colLayouts.map((cl)=>W`<div class="timelineHeaderDay" title="${cl.title}"><span class="dot" style="--border-color:${cl.color}"></span>${cl.title}</div>`)}
        </div>

        <div class="timelineAllDayBar" style="min-height:72px;">
          <div class="timelineAllDayLabel">All day</div>
          ${colLayouts.map((cl)=>{
            return W`<div class="timelineAllDayCell" style="min-height:72px;" @click=${(t)=>{if(this._rnrClickEmptyDayToAddPlus||this._rnrTapEmptyDayToAdd){let ds=null;try{ds=cl.day.date.toFormat("yyyy-LL-dd")}catch(e){};if(this._rnrClickEmptyDayToAddPlus)this._rnrOpenAddPlusDialogForDate?.(ds);else this._rnrOpenAddEventForDate?.(ds);}}}>
              ${cl.fullDay.map((ev)=>{
                return W`<div class="timelineAllDayPill" style="--border-color:${cl.color}" @click=${(e)=>{e?.stopPropagation?.();e?.preventDefault?.();this._handleEventClick(ev.ce||ev,e);}}>
                  ${ev.summary||"(no title)"}
                </div>`;
              })}
            </div>`;
          })}
        </div>

        <div class="timelineBody">
          <div class="timelineGrid" @click=${(t)=>this._rnrHandleTimelineGridClick?.(t,colLayouts,labelW)}>
            ${Array.from({length:hoursShown}).map((_,i)=>{
              const h=startHour+i;
              const rowTop = fill ? `${(i/hoursShown)*100}%` : `${i*hourHeight}px`;
              return W`<div class="timelineHourRow" style="top:${rowTop}">
                <div class="timelineHourLabel">${fmtHour(h)}</div>
              </div>`;
            })}

            ${colLayouts.map((cl,colIndex)=>{
              return cl.timed.map((it)=>{
                const ev=it.e;
                const topExpr = fill ? `${((it.startMin-startMinWin)/winMin)*100}%` : `${(it.startMin-startMinWin)*pxPerMin}px`;
                const heightExpr = fill ? `${((it.endMin-it.startMin)/winMin)*100}%` : `${Math.max(18,(it.endMin-it.startMin)*pxPerMin)}px`;
                const leftExpr=`calc(${colWExpr(colIndex)} + (${it.col} * (${baseWExpr} / ${it.colCount})) + 6px)`;
                const widthExpr=`calc((${baseWExpr} / ${it.colCount}) - 12px)`;
                const timeLabel=`${fmtTime(ev.start)} - ${fmtTime(ev.end)}`;
                const descRaw=(ev.description ?? ev.ce?.description ?? ev.extendedProps?.description ?? ev.ce?.extendedProps?.description ?? "").toString();
                const desc=descRaw.trim();
                return W`<div class="timelineEvent"
                  style="top:${topExpr}; height:${heightExpr}; left:${leftExpr}; width:${widthExpr}; --border-color:${cl.color}"
                  @click=${(e)=>{e.stopPropagation();this._handleEventClick(ev.ce||ev,e);}}>
                    <div class="title">${ev.summary||"(no title)"}</div>
                    ${desc ? W`<div class="desc">${desc}</div>` : ""}
                    ${ev.location ? W`<div class="loc">${ev.location}</div>` : ""}
                    <div class="time">${timeLabel}</div>
                </div>`;
              });
            })}
          </div>
        </div>
      </div>
    `;
  };
'''
s=s.replace(anchor3, fn+"\n"+anchor3)

assert s!=orig and len(s)>len(orig)
out="week-planner-card-plus.js"
open(out,"w",encoding="utf-8").write(s)
print("wrote",out,"(+%d chars)"%(len(s)-len(orig)))
