---
date: 2026-07-20
title: "(EQ) PowerBI Dashboard Check"
granola_id: not_FKQ5hmv2rMygEQ
project: 미분류
type: meeting-transcript
tags: [meeting, granola]
source: granola
status: active
due: ""
priority: med
---

# (EQ) PowerBI Dashboard Check

**Date:** 2026-07-20
**Project:** 미분류
**Owner:** Harim Jung
**Attendees:** Harim Jung
**Source:** Granola (공식 API, AI 미사용 자동 동기화)

## AI 요약 (Granola)

### Power BI Dashboard Overview

- Fully rebuilt dashboard (previous version completely replaced)
- Incorporates feedback from Olia, Brian, TD, and super user meetings
- Three pages: Overview, Stolen Vehicle Alert Analysis, Financial Performance
- Shared via file link for now (not published online)
  - Online publishing deferred: security concerns, visibility settings unclear
  - Open question: how to share more broadly within company (e.g. Tableau Server equivalent)
  - Check with Julia on sharing approach

### Data Reconciliation and Date Field

- Current data sourced from SQL Server export (2025 and 2026 only)
- Must switch all date fields from report date to **event date**
  - Andrew confirmed event date is the agreed method
  - Using report date creates chaos and makes year-over-year comparison meaningless
  - 2026 reported numbers include 2025 and 2024 events, so year-only filter won’t match
- Published 2025 data cannot be changed; 2026 data can use new methodology
- Harim to pull event date field from the model and update data source after the call
- Validate numbers against existing dashboard before August demo
  - Discrepancy is expected but root cause must be understood
  - Use “as of all years” total to reconcile cross-impact figures

### Data Refresh

- Current export is from April/May; now July 20
- Refresh to be done today (Jung So to action)
  - Use July 20 as cutoff; refresh again by end of August for final demo data
  - Harim to update dashboard immediately after refresh is confirmed

### Page 1: Overview Dashboard

- Metrics to keep: total investigations, close with impact, impact rate, average score, total impact
  - Reorder KPI cards to show the funnel logic: investigations → close with impact → impact rate → average score → total impact
- Rename “fraud confirmation rate” to **impact rate** (close with impact ÷ close investigation)
  - Format as percentage (currently showing as decimal)
- Rename page from “Fraud Investigation” to **Alert Analysis Dashboard**
- Remove: funnel value by stage (meaningless after event date switch; investigation count can exceed qualified)
- Remove: monthly trend chart (impact rate trend vs. alert volume don’t share the same date basis; revisit later)
- Remove: total recovered (no meaningful relationship to fraud cases in this context)
- Remove: average days to close (executives requested removal; TD wanted it, but leadership overrides)
  - Keep the measure in the data model in case it’s needed later
- Filter for “close with impact” cases only; remove other workflow state buttons to avoid confusion
  - Add “Close with Impact” to the title/subtitle so audience understands the scope
- Multi-select filter fix: turn off “single select” under slicer settings so users can select multiple months without holding Ctrl

### Page 2: Stolen Vehicle Alert Analysis

- Scope: 44 alerts, stolen cases used for fraud (not all stolen vehicles)
  - Clarify in title: avoid using “CPIC” alone as it implies broader CPIC data
  - Proposed title: **Alert Analysis Based on CP Database** (or similar)
- Keep: top 10 claim type/make-model volume, scenario breakdown
- Remove: heat map (loss time has no relationship to theft time; no theft time data available)
- Remove: cross-province rate for now
  - Definition unclear: report province vs. first-party province vs. CPIC location code
  - Need to confirm with Brian what he actually wants to compare before building
- Remove: financial impact amount (same limitation debate as page 1; remove for consistency)
- Map chart: city/province fields don’t render in Power BI without postal codes
  - CPIC data has location info with postal/FSA codes
  - Jung So has a postal code lookup table in SQL Server; Harim to join on that
  - Replace heat map with a map chart using police city or police postal code
- Format fixes needed: score as integer (0 decimal), amounts with dollar sign
- Page still needs more thought on what story to tell; revisit after event date refresh

### Page 3: Financial Performance (Parking Lot)

- Intent: show money saved (total potential loss vs. total paid)
- Issues identified:
  - Total paid already reflects fraud action taken (declined claims), so net loss understates avoidance
  - Avoidance value is the meaningful metric, not net loss
  - Total paid varies across members and may not reflect final settlement amounts
  - Largely duplicates page 1 summary metrics
- Decision: park this page for now; revisit if bandwidth allows after pages 1 and 2 are finalized

### Financial Impact Dollar Values (Unresolved)

- Ongoing disagreement between stakeholders:
  - Julia wants dollar values included
  - Others (Olia-side) want them removed from EQ Insights
- Core limitation: impact amount only covers claim side; premium-side risk is excluded, so totals underestimate true impact
  - If premium is added, amounts become distorted
- Current recommendation: remove dollar impact for now; explain the limitation if asked
  - Value report already publishes these figures separately

### Member vs. Consortium View

- TD and some stakeholders want member-level breakdown; leadership wants consortium-level only (no “versus” view)
- High-level count by company (e.g. how many alerts per member) may be acceptable
  - But interactive table filters would expose member detail unintentionally: not safe to add without row-level security
- Decision: do not add member-level breakdown for now; keep consortium level only

### Next Steps and Upcoming Meetings

- Harim: switch data source to event date, pull event date field, reconcile numbers
- Jung So: refresh the SQL Server export today (July 20 cutoff); share police postal code lookup table for map join
- Jung So: share to-do list with Harim after this call
- Wednesday 10 a.m.: Harim + Jung So sync to review refreshed data and revised dashboard
- Thursday afternoon: meeting with Julia to align on dashboard direction


- **Switch dashboard data source to event date** (Harim)

  Pull event date field from the model, update all date-based metrics, then reconcile numbers with Jung So.

- **Refresh SQL Server export and share postal code lookup table** (Jung So)

  Use July 20 as cutoff; notify Harim when done so dashboard update can start immediately.

- **Share to-do list with Harim** (Jung So)

  Promised after this call.

- **Set up Wednesday 10 a.m. sync (Harim + Jung So)**

  1-hour block to review refreshed data and revised dashboard before Julia meeting.

- **Set up Thursday afternoon meeting with Julia**

  Align on dashboard direction and date methodology after Wednesday sync.

- **Check with Julia on Power BI sharing approach** (Harim)

  Determine whether online publishing or another method is viable for broader stakeholder access.

---

Chat with meeting transcript: [https://notes.granola.ai/t/b018b3f3-a9e1-4cec-b415-a86e6af8a58f](https://notes.granola.ai/t/b018b3f3-a9e1-4cec-b415-a86e6af8a58f)

## Transcript

**Harim Jung:** Him.

**상대방:** I'm still bringing fire.

**Harim Jung:** Being.

**Harim Jung:** Fire.

**Harim Jung:** The power bi.

**Harim Jung:** Actually the power bi has been totally updated so I'm going to go through the latest version of like dashboard today.

**Harim Jung:** Okay just to show the greatest yeah sure sure link yeah.

**상대방:** Okay, just to show the latest on that.

**Harim Jung:** Hi say.

**Harim Jung:** All right so maybe I can actually start from my end and then so then you can also go over from your power bi dashboard if you don't mind.

**상대방:** Shade of fire first.

**Harim Jung:** First yeah sure.

**Harim Jung:** I will share through the link chat.

**Harim Jung:** Can you see the screen.

**Harim Jung:** I have a quick question Harim stop for power yeah we don't have like.

**상대방:** I have a quick question, Harim. So for power bi, we don't have like how to say it's like an online version, right, like tableau online that we can put it on the server and everyone have a link instead we can only share like this why.

**Harim Jung:** How to say it's like an online version right like haplo online that we can put it on the server and everyone have a link is that we can only share like this body or that's actually a very good question I know we can actually save it power bi account but I'm not sure it's going to be hide and visible like a couple of public that's why I'm a little bit reluctant.

**상대방:** Or.

**Harim Jung:** Okay.

**상대방:** Okay, gosh yeah, but I think this is a good way because it is like a from a security perspective is just like offline right just think just thinking a lot like moving forward how we can share within.

**Harim Jung:** Go try yeah but I think this is a good way because it's like from a security perspective it's just like offline right just think testing out like moving forward how we can share.

**Harim Jung:** The company or you know just like we did for the server like temples or like or we can modify or add it so that we can like work on it together so just an open question go ahead no no no the reserves a good point because I already thought about it because the architecture share it to the like working group or like stakeholder meeting but yeah yeah I think this is a good point I will save it and then like check it with Julia and this is totally a new version of like draft I made it so previously shared one is like completely not a like this you can actually tell this is totally new version because I really want to check based on the olia like command and our super user like meeting with brian and also like TD what they want to see is based on like this dashboard version so I want to go through and number and alignment everything is so like a messy but I'm still working on it so let's talk about like a storyline first and then I will if you have any question please go ahead with me.

**상대방:** The company or you know just like we did for the server like table server like or we can modify or add it so that we can like work on it together so just an open question okay you can go ahead sorry.

**상대방:** Yeah.

**Harim Jung:** Would be fine.

**Harim Jung:** Chris yeah just to clarify for for the current version it has it incorporated with the feedback we want incorporated all of the feedback that's why everything has been updated yeah okay thank you yeah.

**상대방:** Just yeah just to clarify for for the current version is has it incorporated with the feedback or not?

**상대방:** Okay thank you.

**상대방:** Yeah.

**상대방:** Yeah please go ahead sorry.

**Harim Jung:** Please go ahead yeah so actually the previous one is actually one and two pages for.

**Harim Jung:** That sorry my mouse is not working okay so it's a completely different based on like compared to the tablet one but based on like a brian td the very first page is actually how to program and how do things are actually working on so this is actually showing the overview and the second page is like a stolen like cpic based on like a stolen analysis they want to see the top 10 and there was specifically see especially focus on still a little one and third one is actually specifically recursive by the TD especially they want to check.

**Harim Jung:** How actually this one is saving our money or how we can actually eventually like saving and where should actually focus on like investment wise you know so that's why I want to bring up this idea with you so let me go through one by one on the first page okay.

**Harim Jung:** Yeah so.

**Harim Jung:** We can see here like last workflow status like I just click on the close impact one but we already like I already.

**Harim Jung:** Put all of the data source and also the model has been a little bit changed as reconstitut we have to decompose the data model like this so I don't think this is to be honest like perfect model because we don't know how the data set is going to be if we actually get post connected DV so more likely factor larp this one is like what we have and what I what we actually like on the same page from our SQL server so all of the field is actually based on that and I export it and then like slots and dice to make the new model so don't worry about it and it's already included inside of power bi dashboard so you can go through like in detail.

**Harim Jung:** So first of all yeah I only like check the 2025 and 2020 year that's why you don't make sure like 92 total learns and year is only for like two years and also the photo confirmation rate is I made a calculation in here.

**상대방:** Percentage.

**Harim Jung:** This is the percentage so then even yeah yeah no worries just I will yeah I am actually working on all of the presentation like detailed things but just want to confirm this is actually right approach or not so we will eventually show the total largest like for instance 92 case of bacterial loss we found it from the closing path and 15 percentage is like fraud confirmation rate and based on this one we got like almost like a 3.2 like total impact and adversaries sorry sorry.

**상대방:** I then add a percentage.

**상대방:** Sorry sorry yeah so I'll have a quick question regarding 15.

**상대방:** Is it's out of the total close with impact person close with impact right.

**Harim Jung:** It's out of the total close with impact person close to its impact.

**Harim Jung:** Right.

**Harim Jung:** Yeah.

**Harim Jung:** So out of those.

**상대방:** So out of those.

**Harim Jung:** Close ways impact and then you just remove the no fraud.

**상대방:** Close with impact and then you just remove the no fraud.

**상대방:** Oh no it's like cause with impact out of close investigation.

**Harim Jung:** Oh no it's like close with impact out of close investigation.

**Harim Jung:** Yes it is.

**Harim Jung:** Okay yeah because like 50 some low to me if we divide it by close impact but if it's close in time and no impact that makes sense so this is the impact rate yeah yes yes I I need to change all of the name so just don't worry it's like a give me as much as you can as many as feedback so 10 or 0.15 this is 15 percentage this is actually I didn't put any like percentage yet only just like a divided like number as you can tell just update the format 2% but it's like under this measure to and get broad confirmation is shown I mean the cross infected well by today.

**상대방:** Oh okay yeah.

**상대방:** Because like 50 some low to me if we divided by.

**상대방:** Closed impact but if it's close impact and no impact that makes sense so this is the impact rate.

**상대방:** 15% or 0.15%

**상대방:** You can just update the format 2 percentage it's like under this measure 2 and then broad confirmation is which on I mean the close impact by what number did you use.

**Harim Jung:** How this one like a close one.

**Harim Jung:** Closed yeah so it's the intact rate yeah yeah.

**상대방:** Closed so it's the intact rate.

**상대방:** Yeah.

**Harim Jung:** Impact divided by close.

**Harim Jung:** Yeah so I would recommend we make the name of the matrix.

**상대방:** So I would recommend we make the name of the matrix.

**Harim Jung:** Consistent so we can update to impact rate that would be great so that we know.

**상대방:** Consistent so we can update to impact rate yeah that would be great so that we know.

**Harim Jung:** All right because they are more familiar with the yeah total make sense yeah.

**상대방:** Because they are more familiar with the yeah that.

**Harim Jung:** And regarding the total allures is the total okay never mind because you you apply the filter here okay yeah they don't want to actually see the 2024 data source so yeah so the impact rate is like 15 percentage and total alert is 92 and like a base on this one total impact is like 3.2 million but I just put it just for internal cases because they don't want to see the impact number from the startup like a routing pack like a total paste right so a little bit moving and I want to show the oh yes go ahead.

**상대방:** And regarding the total allures is the total okay never mind because you you apply the filter here is the closest impact okay sorry.

**Harim Jung:** Yeah sorry just before we move forward I just want like know here is that.

**상대방:** Just before we remove for like just one like a note here is that we also need to reconcile the data right.

**Harim Jung:** We also need to reconcile the data right between this one with the dashboard that we shared because they will be surprised if we share.

**상대방:** Between this one with the dashboard that we shared because they will be surprised if we share.

**Harim Jung:** A different value and that they would ask me how we reconciled what the numbers so my question for the August demo we should we let them know this is the real data or this is just the testing data.

**상대방:** Different value and then they would ask have we reconciled the what the numbers so to my question for the August demo we should we let them know this is the real data or this is just the testing data.

**상대방:** Because if we want to show them the real data then we there is actual step that we need to do to validate the number before we share with them just just we should use actual data.

**Harim Jung:** Because if we want to show them the real data then we there is actual stack that we need to do to validate the number before we share with them just what we should use to add in the dashboard and today I pick the files you should take discrepancy and then this point we should use the reaction data and that's clicker system with our current number.

**상대방:** After creating the dashboard after they found huge discrepancy then there is issue.

**상대방:** So at this point we should use the actual data and that should be consistent is our current number.

**Harim Jung:** Yeah okay just for like clarification I am using the our like DB like SQL server connected data source that just exported. So from my perspective this is real data or am I yeah.

**상대방:** Okay yeah.

**상대방:** This is actual data.

**상대방:** Sorry the year is 2026 and 202.

**Harim Jung:** Sorry the year is 2026 and 2025.

**상대방:** 0.

**상대방:** Five the number.

**Harim Jung:** The number.

**상대방:** This now right to me if you want to compare the number then we choose 24 25 26 all of those because our numbers are an event there right so if you compare with this one we should use all use.

**Harim Jung:** Does not write to me if you want to tell you compare the number then we choose 24, 25 and 6 workbooks because our numbers are prevented.

**Harim Jung:** So to compare this one which use all you.

**상대방:** Oh yeah this also remind me another question is regarding the year that we use here what we should use.

**Harim Jung:** Oh yeah this also remind me another question is that regarding the year that we use here what we should use.

**상대방:** Because.

**Harim Jung:** Because.

**Harim Jung:** Previously we share like the proposal with Andrew and Andrew want the original method right then the days that we use there is the event date.

**상대방:** Previously we share the like the proposal is Andrew and andrew want we stick with the original method right then the year the date that we use there is the event date.

**상대방:** Yeah so if you use a whole number.

**Harim Jung:** Space include yourself whole number.

**상대방:** Then.

**Harim Jung:** And it's reconstituting customer.

**상대방:** HTTP consider constant is.

**상대방:** Our number but if they want to just want to see this year but event day basis just compare with that one.

**Harim Jung:** Non-par but if they want to just want to see this year but event day basis just compare with step one.

**상대방:** If you do if you want to think that way then we should change all of the data period into event date but create chaos in our data.

**Harim Jung:** If you want it in that way and wish to change all of the better period into event day. But that created chaos in our data.

**Harim Jung:** So I have a question two checked it like a data validator do you think like a data validation first and then like go to check with the dashboard is a better idea or go through the dashboard and then tip with this currency and the data validation is better.

**상대방:** Just to checking the whole whole year as of the whole a lot.

**Harim Jung:** Just to technical year has all the whole a lot. And as of this point in that terms we compare the number then we can compare.

**상대방:** As of this point.

**상대방:** Yeah in that terms we compare the number then we can compare.

**상대방:** The cross impact that should be same as the one we have in the.

**Harim Jung:** Cross impact that should be service the one we have in.

**Harim Jung:** The our dashboard number that also used to be including as of everything has all.

**상대방:** Our dashboard I was reported number that also should be including as of everything as of.

**Harim Jung:** The children. So in the terms then we assume that this is okay.

**상대방:** The Jung end of two or something like that so in the terms the taller number is same then we assume that this is okay.

**Harim Jung:** And if it just to match.

**상대방:** But if just.

**상대방:** Match with 26 only then there is a problem because 26 quadrilateral dam 25 was summer 24.

**Harim Jung:** 26 or me then that is problem because in 26 kind of from 25 or 24 then actually all of those matches actually the doors are not in the proper.

**상대방:** Then actual all of those metrics actually that also not appropriate inappropriate.

**상대방:** Another noting here is that we also have published some 2025 deaths already.

**Harim Jung:** Here is that we also have published some 2025 dance already.

**상대방:** So for those like published the data we cannot change it but for the 2026 data we can.

**Harim Jung:** So for those like accomplish the data we can now change it but for the 2026 data we.

**Harim Jung:** Can use massive dollogy so but I think I can share.

**상대방:** Use new massive dollogy so but I think I can share the dashboard that I built later and so that we can sell them together so sorry 26 26 or so problem I mean in our reported number in 26 that also included 25 or 24.

**Harim Jung:** The diaper that I built later and so that retails nailed them together so started 26 26 wholesale program in our report and I'm very 26 that was included 25 to 24 right.

**상대방:** Right yes even means that we cannot compare 202.

**Harim Jung:** Yes we can compare 2067.

**Harim Jung:** When we just compare the whole year of the burn and this number unless we look at all of we cannot match it.

**상대방:** We just compare the whole year for the order number and this number unless we compare whole number we cannot match it.

**Harim Jung:** I see.

**상대방:** Yeah but we we need to do that we can it's okay we have discrepancy but we need to know what cause that discrepancy so that because there might some clear.

**Harim Jung:** We need to do that it is okay we have discrepancy but we need to know what counts the discrepancy so that because there might be so clear.

**상대방:** You know that our our the published number used event.

**Harim Jung:** You know that our the published number used animatic basis.

**Harim Jung:** That's the only reason.

**상대방:** There's only reason.

**Harim Jung:** So how like regarding like that is currency how can I wonder how can I show like.

**Harim Jung:** Figure out you already mentioned the discrepancy resonance are very clear how can I show like a figure like a solvent because you're like maybe one thing I think that.

**상대방:** So maybe one thing I think that.

**상대방:** We need to see if we change it to event date is it okay to show it maybe it also showed the number so maybe they might consist on with that one but in that case for example.

**Harim Jung:** We need to see if you pretended to invent the aid is it okay to show it maybe it also show the number so maybe consistently step one that in that case a crucible.

**상대방:** The the impact rate that has no meaning that.

**Harim Jung:** The impact rate that has no meaning.

**Harim Jung:** Because some.

**상대방:** Was some.

**Harim Jung:** APUs impact on even in fact close to close the case.

**상대방:** EPUs impactful even in impact rate.

**상대방:** Close the case.

**상대방:** Was last year.

**Harim Jung:** Was last year.

**Harim Jung:** Right then in peck rate a little bit complicated.

**Harim Jung:** So I would suggest that we just switch to event date I see that would be make the service okay okay I will change you to the event date yeah after this call I will change the data like sourcing a bit and then keep the alignment as much as I can and then check the discrepancy together with you so if you if you're available and then yeah so overall yeah then this one is a little bit like minimalist but yeah we can show that like a total alerts and hopefully have a like impact rate we can show and total impact and average score and also I just want to show like a total recovered like a large number of like a totally covered here an average date to close one so all of the like this one under number is going to be like height but I just like to make them visible to go through together with you and they want to see like a burst of climate policy breakdown based on like a total loss and alert volume by the year but I think this is like a quite meaningless I want to show like at least like quarter by quarter so we can see which quarter which decision must but which quarter we have a majority of like our volume is like alcohol and also.

**상대방:** So I will suggest we just switch to event date that would be then make the make the impulse.

**Harim Jung:** The major insight is like based on the scenario you can see majority is actually from like a based on the ship one right and.

**Harim Jung:** Here like a financial impact by the scenario ship is like almost like 80 percentage of like a bite all of like a total alerts so which means more likely ship to ship means like related to stolen or like shipped to the like average like the major like amount for like alert so this is like the biggest like the risk in here and also based I want to check this one with you guys so I just made a final value by the stage and how I actually calculate the funnel values.

**Harim Jung:** I think that if you change it will be maintained all number you can seriously so yeah but you can say if you can do it here is that just for the component there is a problem other than the number of numbers in the shape I see I see a total makes sense yeah but I just want to ask you and young soft like regarding like funnel this is our summation from the meeting they want to see the stage so do you think this approach is like a right approach especially for the funnel stage I wanted to show from the start and qualified and investigated and impacted.

**상대방:** I think that if you change the event data all number will be shaken seriously so we can say anything but if you can do here is that just for the component if it is there is prop or not other than the turn I mean the mode of numbers will be shaken.

**상대방:** Which one are you talking about?

**Harim Jung:** This one funnel value viral stage so just like regardless of like a number we want to show like out of like 92 like alert it but oh yeah no this one is has no meaning actually because taken from different a lot in the other allotted in the qualified you mean allotted to qualify investigation from qualified.

**상대방:** This one is has no meaning actually because different from different a lot in order allotted in the qualified allotted the qualified sleep allotted.

**상대방:** Right investigation should be from qualified.

**Harim Jung:** I see but if you send it to the event today all those are preached so you can see I mean.

**상대방:** In that way right but if you select the event date all of those are crashed.

**상대방:** So we cannot see I mean.

**상대방:** The investigation might be larger than qualified.

**Harim Jung:** The investigation might be larger than quick but after that no we can tell just want to ask youg so I this is actually mentioned from the brian he wanted to see some like stage regarding like a funnel kind of concept do you think at the re-updated data like basically the event day this final kind of approach is like not not bring us any insight or do you think it might be okay because I want to check yeah even actually it will event that then we cannot actually have nothing to say but but anyway they want we can do.

**상대방:** One.

**상대방:** So we need to see the number right so after then we can tell this is before now.

**상대방:** Even actually if it event date then we we cannot actually have nothing to say.

**상대방:** But but anyway they want we can do.

**상대방:** But.

**Harim Jung:** But.

**Harim Jung:** You know maybe sometimes that number might be okay but sometimes at some point it might be a people's way so at that time you make us crazy I understand and also the one request is actually top 10 vitam volume so especially by the claim type so we can see theft or of like entire vehicle is actually like a very private pretty high from this one but I think it going to be it might be a subjected and also this is a simple like a financial impact better scenario so we are very good check from like a based on the ship scenario majority like impact alerts are actually come from like this scenario and this is a new chart I want to actually show because usually I want to keep some visually appealing but power bi has quite variatic design limitations so I just want to bring it up this one so based on the scenario and personality the second category is like prevalence and the third one is a claim code and the last one is like investigation reserved so if we click on like a ship and for instance like ontario we can see the specific like numbers and those are actually known value and previously I could map it out like roughly as angel requested because they don't want to show any null value but I don't think I can I should have distributed all like manipulate data from here so just a little bit away.

**상대방:** Yeah maybe sometimes that number might be okay but sometimes at some point it might be in reverse way right so the debtor make us crazy maybe later.

**Harim Jung:** But just want to show like how this chart is actually showing.

**Harim Jung:** The like flow something like a sand key so do you have any idea or do you think it's like it might be meaningful or not?

**상대방:** I think that we kind of like there was debating on if we should include financial impact or not because from last thing I remember having mentioned that that you know like we should remove the you know like the values from eq insights but from Julia's perspective she wants to include the dollar values because she mentioned we can not only tell from the volume but we can we also to check the.

**Harim Jung:** I think we kind of like there was a debating on if we should include financial impact or not because from last thing I remember having mentioned that you like we should remove the values from the community sites from Julia's perspective she wants to include the dollar values because you mentioned we can not only tell from the volume that to check the.

**상대방:** Value so I think we don't have I don't think like from this two perspective we don't have like a rich rich to alignment on if we should include the impact or not.

**Harim Jung:** Value so I think we don't have I don't think like from these two perspectives we don't have like a rich to alignment if we should include the impact or not. Yeah I also agree with that.

**Harim Jung:** And so you're right I think that you have some reasonable ground for this topic because.

**상대방:** You're right I think that has some reasonable ground for is token because especially the policy side the detection has very low.

**Harim Jung:** Especially the policy side detection has very low.

**Harim Jung:** Amounts might be more than enough just a premium from them they might be risk so just use the mount and put everything then this problem we just select who we just complained to this thing to claim side claim only and that has meaning but if you have a premium clean gateway everything and with just you can come out then the amount might be distorted.

**상대방:** Amount but actually actually impact might be more than that not just premium right if there is claim from them they might be yeah there's risk so use the impact amount for everything then this problem we just select we just combined to restricted to claim side claim only that has meaning but if you add a premium claim that way everything and with just input amount then the amount might be distorted.

**상대방:** Right.

**상대방:** So maybe counter is okay actually.

**Harim Jung:** So when the country is okay.

**상대방:** But why do I would suggest live stream remove for now and then we can explain to you then why we did not include it and also we we report the value in the value report already right so we can if you really want we can add it but let me explain it we need to add that that each that issue so the amount have some limitation this might undergrad underestimate the actual impact.

**Harim Jung:** But by the way I would suggest light removed for now and we can explain to you then why we did not include it and also we report the value in the value report already so we can watch we can have it but we need to add that is that issue.

**Harim Jung:** So the amount of harvest limitation underestimate the actual impact.

**상대방:** So let's remove for now or maybe yeah.

**Harim Jung:** So let's remove for now maybe yeah yeah great to remember that and the other one I found in the dashboard is that.

**상대방:** Agree and then they might decide whether we will not and then the other one I found in the dashboard is that this is a multicellular right?

**Harim Jung:** This is the multi-select right yeah but if you click it is almost like the radio button just select single simple single select in order to select more than one is to create control right yeah you can actually get press control key and even in months in order to select all of the 12 months which should be selected each one oh yes so can you please this is easy to change your soul can you please go to the setting yeah no right so making that way the user standard experience there is under the selection yeah there will be on with multi slack with comment so you can turn it off.

**상대방:** But if you click it is almost like a radio button just select single simple single select in order to select more than one was to click control.

**상대방:** Right.

**상대방:** Yeah even even in months in order to select all of the 12 months we should select each one.

**상대방:** Oh yes so can you please this is easy to change your soul so can you please go to the setting 10 megaposit in that way I mean the user be able to experience that there is under the selection so under the selection yeah there will be I'll and there is on with multi slack with comment so you can turn it off.

**Harim Jung:** The second one after the under the selection the second one you can turn it off and then it can you can click that try yeah then what's the man yeah so so we also can set floor for individual.

**상대방:** The second one after the under the selection the second one you can turn it off and then it can you can click that try yeah yeah that's the way yeah much better yeah so so we also can set all or individual one right okay yeah.

**상대방:** Okay that's good.

**Harim Jung:** Okay.

**Harim Jung:** So I also want to ask you this one maybe is just for now just like a.

**Harim Jung:** Leave all of the last workflow state.

**Harim Jung:** Right to check yeah how to think about it just just for because this is another pleasure that I have like this I want to discuss with you guys that for the dress we want only so close with impact cases create all the butter that the keyboard completion just just so that maybe they look this yeah yeah yeah yeah and then maybe for a total years and they just mentioned that this is totaled total close with impact alerts yeah okay so during the call we can let them know that for the body part we still developing right given the pipeline because they set up the call.

**상대방:** This is another question that I have like for this I want to discuss with you guys during this call is that for the draft do we want only show clothes with impact cases yeah only this one if you create a activate all the button that they might give us confusion so just just do not maybe remove this one yeah yeah and then maybe for a total alerts and then just mention that this is totaled total close with impact alerts yeah right yeah.

**상대방:** And then during the call we can let them know that for the other part we still developing right given the pipeline because they set up the call on.

**상대방:** All the stuff.

**Harim Jung:** All the.

**상대방:** Which they ate or yeah the week off the august 11 that week so it's pretty close.

**Harim Jung:** Eight or yeah the width of the August 11th that week so it's pretty close.

**상대방:** And two weeks maybe the close impact that one you'd rather put it in the title in the third line.

**Harim Jung:** Maybe close in fact that one you drive it put it in the title in the third line okay okay yeah so that they can identify easily in the pygmy right I'm not putting a note and change it yeah no well I am actually checking everything right now so I am like writing down some notes as well so it looks like yeah thank you and also I just read to do list as well so I'll share with you yeah and also for the another one is that just have the note from the meeting last time that they won't name the forward warning to alert analysis right so I wonder for this page we rename it as just alert analysis dashboard instead of fraud investigation yeah okay then the other type like students CP analysis is not good student as.

**상대방:** Yeah so that they can identify easily in the beginning right yeah.

**상대방:** Most impact on something like that.

**상대방:** Yeah yeah thank you and also I just read some to do list as well so I'll share with you Harim after this call yeah and also for the another one is that just scan the note from the meeting last time and they want renamed the fraud reporting to alert analysis.

**상대방:** So I wonder for this page should we rename it as just alert analysis dashboard instead of fraud investigation yeah more clear for the ranges right and the other title like stolen CP analysis is not stolen that stolen car right.

**Harim Jung:** Well.

**상대방:** They mentioned that they won't use the stolen dash is the big yeah.

**Harim Jung:** To mention that they won't use the big yeah this is also quite complicated how should I how should you actually put that they want to put the same big word but yeah maybe you know the taste is competent story yeah I upgrade as well because we use the cp2 generates other reports like auto trends this got confused because this is the start because they keep us asking you like is this the civic data is right?

**상대방:** You know the city is you know this is competitive story.

**상대방:** Yeah I agree also because we use the cp2 generate other reports like auto trends in session right then this got confused because this the start because they keep us new like is this the civic data or the eq insights right they have so what about we just mentioned stolen vehicle a lot a lot we call alert analysis based on cpeak database.

**Harim Jung:** So what about we just mentioned we are cold alert analysis based on cp database yeah.

**Harim Jung:** Yeah.

**상대방:** Yeah.

**Harim Jung:** So I would like to make it smaller okay I will work on this one yeah they make small the mapping the second line or maybe small.

**상대방:** They make a small based on the they might be in the second line or maybe tomorrow yeah and then just mention the stolen stola we call alert analysis yeah.

**Harim Jung:** And then just mention the stolen we are called a lot just alert yeah so they will learn analysis.

**상대방:** Yeah so they will yeah alert analysis yeah.

**Harim Jung:** Yeah okay the first page I will just remove this one and I think they're more likely the most important thing is actually messing with the event dates so they the number is going to be entirely changed but I will work on it and then like I come back to you so I want to check it one thing I want to ask right so even this one I don't think is that meaningful after we actually like change the event date especially I want to check the total alerts and impact rate but yeah I understand you have the data event today right in the record yeah we have it okay simple to change it.

**상대방:** Yeah.

**상대방:** The data event today right in the record.

**상대방:** Okay then it might be simple to change it.

**상대방:** Yeah yeah because also you create event date so yeah correctly use it so that's really easier for us.

**Harim Jung:** Yeah because you also you create event state so yeah correctly use it I didn't actually pull the event date from our model so I need to go back and just like pull again yeah don't worry you can add it back yeah.

**상대방:** Yeah right you can add it back yeah.

**Harim Jung:** So just take close of them in the table so that if you want can you see we don't need to Etc. Okay I want to confirm so from now on our throttle reporting related all the data we are going to switch the event date.

**상대방:** So in the data if possible just take those of them in the table so that if you want you can use it we don't need to extract it again but if you force again.

**Harim Jung:** Right yeah if it is then all proceedings I see I yes okay we have that in the database the wheel that Jung so created called the real some learn summary ID that that will you can use that and then for the for the close the investigation you can join join to that inner join and then we can have okay okay in the future yeah I will join them it's better yeah I don't want to lose some column so okay last time I I'm I'm not sure completely the tech I wanted to see bi-monthly so you see the teaching increase adviser the monthly alert yeah yes monthly yeah this is a monthly date yeah alert Trend oh okay yeah yeah but I think that if you just bust as one to trap you can do it okay yesterday here here months test being around in alternate wonder Jung so because our data data set especially for 2026 is quite like out not outdated but not actually collecting all of the data sets so if we just showing the only the months like number would it be fine.

**상대방:** Oracle event date yes we have that in the database the way that Jung so created called the wheel some lore summary ID that that will you can use that and then for the for the close the investigation you can join join to that inner join and then we can have.

**상대방:** More either for join in the future.

**상대방:** Yeah yeah.

**상대방:** Last time I'm I'm not sure the company name the tech I wanted to see bimonthly so he said did you include that one?

**상대방:** Yeah monthly they wanted to see monthly.

**상대방:** Right.

**상대방:** Okay yeah but I think that if you just months as one to 12 you can do it H3 year year month there should be no item list.

**상대방:** What was stressful what about we remove this first because.

**Harim Jung:** Who's stressed out what about we move this first because.

**Harim Jung:** One that must be a large trend just thinking up on here because this is more like more like an impact rate trend right but this is monthly thinking because it does not match at all right because you a lot should be based upon Haratim yeah.

**상대방:** There must be a lot of trans and flawed raid just thinking a lot here because this is more likely more like impact rate trend right yeah this is monthly this is really tricky because it does not match at all right.

**상대방:** Because you know a lot should be based upon a lot to you.

**Harim Jung:** But through the trend rate there is not based on.

**상대방:** But the trend rate there is not based on thesis event so there is crazy that that's what I'm saying.

**Harim Jung:** The radio this is event take place it's so easy it turns crazy this is what I'm saying yeah both of our last remedies for now and then we can think about later if we need to just remove the dashboard and let's see that graph and the decide whether to include the total claim tax that one.

**상대방:** Yeah what about let's remove it for now and then we can think about later if we need yeah just just let me put the dashboard and then let's see let's see that graph and then decide whether to include or not yeah and there regarding the total claim tabs that one.

**Harim Jung:** There is a challenge part here regarding this is the it need export from.

**상대방:** There is a challenge part here regarding this is the it's needed to export from.

**상대방:** The platform because this is now available from our database.

**Harim Jung:** The platform because this is now available from our database it's additional field right this is actually tricky I mean for the fraud so this is no relationship is fraud just to claim as it is but the case is important so so let's remove it relationship with sexual property what if like we change the claim cost clean to the suspicions no because they want to see the.

**상대방:** It's additional field this is actually tricky I mean does not show anything for the fraud right so this is no relationship is fraud just claim as it is but the case this is in plot it so so let's remove it I suggest less less relationship.

**Harim Jung:** Top some volume actually that's why I just keep the top 10 yeah this one is actually the by scenario is the one if you create yeah and also it meant like share more information right which scenario performs best or which scenario has the most cases right most value let's say from either pandemic or this is upon crossing pet just order by the snare okay I will keep this as yeah virus scenario like we call like suspicious here so okay so Jung so can saying we decided not to share monthly one right so I just like removing and also another one is regarding the average days to close that one all kind of information wants is press here like what kind of insights do we want to share is directly new like yes take long to yeah like being most important information yeah but they also don't want to blame the members like that we want is private information on you know you are reviewing this members to finish as soon as possible I see but I remember I I forgot his name but specifically he want to see the how long it would normally take.

**상대방:** Yeah this one is actually the by scenario is the one.

**상대방:** If you if you create one scenario they might move appropriate yeah and also it might like share more information right on like which scenario performs best or which scenario has the most cases right most value let's say from either parad damage or so this is one thing yeah based upon based upon close impact yeah just order by the scenario that might be better.

**상대방:** And also another one is regarding the average days to close that one what kind of information do we want is press here like what kind of inset do we want to share is like you like it take long to yeah this might be also important information yeah but they also don't want blame blame the the members like that we want we don't want is pride information on you know you are reviewing this map increase the members to finish only as soon as possible.

**Harim Jung:** So to detect the you know from the starter end that's why I just said keep it but there's actually but always like two opposite like fit a service come someone to show the dollar value some doesn't want and some want to see the you know very precise like how long does it take and some people just want so it starts good good calling and Jung so for now we can actually remove it right.

**Harim Jung:** There's the average days yeah.

**상대방:** This is I think this is important information because in operation side this is important information especially our data is in the event databases right in that case there is a link between the data and the detection period.

**Harim Jung:** This is I think this is important information because in operation side this is important information especially our data is event crisp cases right in the case that there's a lag between the data and detection purity so because of that if you don't want definitely can be but I think that this is one of the important operation information.

**상대방:** So because of that if urea and territory want definitely we can remove it but I think that this is one of the important operation information.

**Harim Jung:** I see.

**Harim Jung:** Yeah because I remember last time when we discussed that they want remove it just from the nodes okay.

**상대방:** Yeah because I remember last time they when we discussed and they want to remove it just from the notes yeah.

**상대방:** Okay whatever you want yeah that's a problem last like a meeting note with like do you remember we have a meeting with them first right and then this is wrong then needing no one remove it yeah this must show that they are a little lazy in the handling this one so maybe they might want show that they are not so active in the handle these cases.

**Harim Jung:** Yeah this is from last like me not with it like you don't have a meaning with them first right and then this is from that meeting now with remove it might show that they are a little lazy handling this one so maybe they might want show that they are not so active in the head cases exactly I want to ask you what what kind of like mainland was it from like our side youli and Terry or the not actually from operations like from the stakeholder.

**Harim Jung:** This one the average day from our from us node right right because because I remember from the TD they really want to see it was TD and make sure they wanted to see their average days you know so that's why so let's keep when they asked us we can say that TV wants to buy right and then yeah we have vision to keep it because we interviewed with TV yeah sometimes we might be to compare these number so we if there's any improvement then we also can say that the processing time is gradually decreasing so they might be put way to show that how our systems can be seriously yeah so actually that average day actually like a pattern was initially developed from our side from our first batch of like a dashboard but our leadership team want to remove the average day pattern but this is quite tricky from my side to decide it so Jung so do you think show the pattern is okay like a meaningful from like operation review then right now we can actually suggest how to think about it.

**상대방:** This one the average day they used to cost from our from Julia's note than to carry yeah.

**상대방:** So let's keep it because when they asked us we can say that did you want to see the so called time right and then yeah we have reason to keep it because we interviewed with cd sometimes women need to compare this number so if there's any improvement then we also can say that the processing time is gradually decreasing so that that might be good good way to show that how our system is used in the member side.

**Harim Jung:** Our exceptives don't want to show it then definitely I see okay yeah so we can we can suggest it but they don't want their I see okay totally makes sense.

**상대방:** Our executives don't want to show it.

**상대방:** Then definitely remove it.

**상대방:** Yeah so we can we can suggest it but they don't want that you can remove it.

**Harim Jung:** Unless we know it's right now and then maybe the asthma and we said that.

**상대방:** Let's remove it for now and then maybe the aspirin and the way said that yeah just put in somewhere but we don't need to show it right yeah.

**Harim Jung:** Yeah just put in so but we'll need to show it right yeah nice see all the sacramental duplicated and remove it okay this is actually the fit a version of like this one oh yeah need to work a little bit more or but it's very simple right yeah then they will have less information and also a quick question regarding what is total regard this is like the stolen vehicle this this is actually from our column you know like a recovered one because it's going to be there yeah.

**상대방:** Yeah then they will have less information and also a quick question regarding what is total regard total recovered it's like the stolen vehicle.

**상대방:** Oh the code shouldn't be there.

**Harim Jung:** Actually there is the issue I mean it's recovered then I'm not sure there is just for those simple cases and there is recover then actually that is not correct.

**상대방:** So actually there is an issue I mean.

**상대방:** If you recovered then.

**상대방:** That I'm not sure there is just photos CP cases and it is recovered and actually that is not correct.

**상대방:** A lot.

**Harim Jung:** A lot because only the one installing.

**상대방:** Because she picked only the one in storm.

**상대방:** Right it is recovered and all that has no meaning I mean we just check the cases with a stolen but there seems like that but if the recovery rate is then the discrepancy among the formation.

**Harim Jung:** Right cover then Har has no meaning I mean we just check the cases it's a sternum but there's a clear this looks like that.

**Harim Jung:** But if you said recovery rate is then discrepancy among the commission.

**Harim Jung:** I say.

**Harim Jung:** About remove this from this analysis maybe we can add like in the stolen yeah and also Harim can you please reorder a bit on the the highlight you know the total rate and then maybe every score and the finally is the impact and then maybe from the total loss and we can also add another one is the total close the investigations because that's our third point right the total investigations then model then the cause with impact and then the impact rate and then average score just like a reorder of it.

**상대방:** From this alert analysis maybe we can add like in the stolen if needed yeah and also Harim can you please reorder a bit on the highlight you know the total loss in period and then maybe every score and the finally is the impact and then maybe from the total alerts we can also add another one is the total close the investigations because that's our start point right the total investigations then told them the cost with impact and then the impact rate and then average score so just like a reorder a bit.

**상대방:** Yeah.

**Harim Jung:** And making it like a green wine so that there will no let's say we start with the close busy both with investigation and then close with impact and then this is how we calculate the impact is based on these two metrics and then is the average score and then it's the total impact.

**상대방:** And make it like a streamline so that they will know let's say we start with the cost with introduce and then close with impact. And then this is how we calculate the impact rate, right? Because impact rate is based on these two metrics and that is the average score and that is the total impact.

**Harim Jung:** I forgot why I remove actually the total investigation things but yeah I will actually put it back I think there's a kind of note yeah okay total hours like total investigation intake rate total impact and average score right okay yeah so maybe if you change the.

**상대방:** Yeah so maybe if you change the.

**상대방:** Data with event related all of those numbers also should be changing. So maybe after then we can see it again.

**Harim Jung:** Data with the event today to all post number also should be changed so maybe we have to then we can see okay yeah.

**Harim Jung:** So more likely lots of things.

**Harim Jung:** So based on like the first page of like overview what they want to see like what they want to see is actually the scenario flow and actually they want to see some trend but we decided not to show them mostly trend.

**Harim Jung:** So what kind of insight could he actually bring it up from like overview page.

**상대방:** Another one is not sure if it's problems to display here the other one is for some member level versus consortium level comparison.

**Harim Jung:** Another line is not sure if it's pronounced this way here the other one is for some member level versus consortium level comparison but so I wonder if we can add in the first page but this will be constrained to the member data right sensitive yeah so there's also two like specific things really got we got from like different like middle notes you know our leadership level just want to see the consortium because they don't want to show any versus person.

**상대방:** So I wonder if we can add in the first page, but this will be constrained to the member data, right? Because it's sensitive.

**Harim Jung:** And Julia want Julia mentioned like versus version she want to put but as long as remember angel say there's no like versus version don't show and the it was brian and no no it was TD they want to see the.

**Harim Jung:** Because they really want to see this like accurate number they want to see the verses so in this case I also want to ask you what would be the best idea the purpose is very simple we can just like calculate it and put it on and we already have like a member name you know fieldy here so do remember like the second.

**Harim Jung:** Person of like a dash tablet dashboard we put a role level security and like a per member we could actually make them see but this one they say no you know not to actually show them like member state so it would be good idea to show the persons and giving the role of like security like kind of approach that each member can see the versus version or just go through the consortium level like as of now.

**Harim Jung:** Maybe even in the concession level might be a high level count might be.

**상대방:** Maybe even in the consortium level might be high level.

**상대방:** Account might be.

**Harim Jung:** Might be okay like come for example we have 92 toner crossing so by company how many cases are there can get a little bit.

**상대방:** Okay like for example we have 92 total gross impact or not.

**상대방:** So by company how many cases are there?

**상대방:** Then that level.

**상대방:** That have very high level.

**Harim Jung:** That have very high level.

**Harim Jung:** So for instance yeah for instance if you actually click on a viva it only show like five proto alerts only for like closing power.

**상대방:** I think.

**상대방:** That.

**Harim Jung:** Oh yeah the problem is that if you edited work there also can be used the filter right yeah yeah that's the problem so maybe in this case like.

**상대방:** Oh you're right that problem is that if you edit that one there also can be used a filter.

**상대방:** Right here that's the problem then we might not add it.

**Harim Jung:** Separate like per members or apply some role level security data is not a big deal we can put some parameter or some different yeah we can remove the pin so here does not only for those it will be okay okay then Jung so even though like giving like a stake order our member to show their number versus consortium would be a good idea right.

**상대방:** Yeah, we can we can remove the filter so the filter does not work only for those then will be okay.

**Harim Jung:** No I see.

**상대방:** Very high level only.

**Harim Jung:** Anybody might want to.

**상대방:** To be viewed by other company for details.

**Harim Jung:** Be viewed by other company for t-test so only the how many lot was impacted by competent only in that level but that should be used as a filter I see I see no worry about the filter so only the high level right yeah.

**상대방:** Only how many lots cross impact by competent only in the event but they still be used as a filter.

**상대방:** Yeah.

**상대방:** Because our whole table is interactively all of those work as filter then unintentionally all of information might be short. All detailed information might be opened.

**Harim Jung:** So our four table is effectively four of those work is orientation on the autoimmune problem is microphone so yeah that's not cool yeah I see I see.

**상대방:** So that's not going.

**Harim Jung:** Yeah another sex can we add a filter for alert tab because different alert have different information so as a filter can we add the alert hack.

**상대방:** To we add a filter for alert tab because different alert tab can have different information.

**상대방:** So as a filter can we add the alert tab.

**Harim Jung:** What is alert?

**Harim Jung:** Yeah alert head the elements tab I believe element tab that's the alert.

**상대방:** Alert the element type I believe is the from the element tab that's the alert.

**Harim Jung:** Time.

**상대방:** Tab.

**Harim Jung:** I see but it's already like here like claiming policy so should you actually do that we can click on it and we can actually filter yeah so you can already click yeah as long as we have something we can actually slice and dice the scenario and hear like high level scenario like different like low level like suspicious level and claiming policy element and we already have it mining the cash card yeah if you click the clay or.

**상대방:** Oh I see so you can already click.

**상대방:** Okay.

**상대방:** We already have it if you see the one in the pie chart if you click the claim all it was created.

**Harim Jung:** Okay then.

**상대방:** That's not a problem you just want to see if we have a way to filter it.

**Harim Jung:** That's not a problem yeah just one see if we have a way to filter it okay never mind.

**상대방:** Okay never mind.

**Harim Jung:** And then the formal value by stage we will remove it right so this is my question I understand then there's not many things we are actually showing and I want to rely on you guys knowledge what kind of insight could you actually bring it out more in here?

**상대방:** And then the final value by stage we will remove it the formal installation.

**Harim Jung:** Because very conservative at some point.

**Harim Jung:** And.

**Harim Jung:** I think that we marinate time we need to think about this way I think that we need to compare with previous one and this one and what I was thinking okay what we are trying to show exactly yeah so within time so maybe one or two days more yeah and then with that refreshing the experience after then we can see we need to turn the time when we need to think out what we are trying to show it is passion yeah yeah I think this is now simple as we check the branding where you test the more format is more on how we can more to show the insides right I think it's now that costing pole that's stable exactly the more iteration we are heading to more the last actually we are showing so yeah I understand okay yeah so okay this is like the first page and let's check the stolen one together.

**상대방:** We need to think about this we I think that we need to compare with the previous one and this one and also think again what we are trying to show.

**상대방:** Yeah so we need time so maybe one or two days more and then with that refreshing the date period after then we can see we we need to turn the time we need to think out what we are trying to show in this from this dashboard.

**상대방:** Yeah, I think this is as simple as we change the branding where you like the task format is more on how we can add more to show the insights right I think it's not like a steam pole that's the whole point yeah.

**Harim Jung:** So like if this is based on like only the step stays only like a stolen cases so this is only 44 and like relate related to the 44 total hours like stolen and large we can show like.

**Harim Jung:** 2.4 million for like impact and this is actually cross province rate.

**Harim Jung:** This is from.

**상대방:** This is from.

**상대방:** Bright okay yeah.

**Harim Jung:** Briar right yeah okay yeah yeah this is from.

**상대방:** And the one from safe timing hit me this is from.

**상대방:** How did you get it?

**Harim Jung:** How did you get.

**Harim Jung:** Set time engagement.

**상대방:** Safe the timing heat map.

**Harim Jung:** Map let me check this at the time period and day so this is usually based on our data source for the I think it will be use the lowest take time for cancer that is just the claim information you know what I'm saying yeah you're right just an ordinary loss but the car is basically already stolen so there are no no relationships you're right because also this is okay sorry go ahead no no no no your right because we don't have actually theft time data right yeah yeah definitely but at some point not only not a theft but is there any like logic or like a story we can actually show something like.

**상대방:** I think that you use the low state time there is no for there is no.

**상대방:** That is just the claim information so you know what I'm saying the car is just an ordinary loss but the car is basically already stolen so there are no no relationship with this tile.

**상대방:** Oh so this is okay sorry go ahead.

**Harim Jung:** More.

**Harim Jung:** People like a deeper level of.

**Harim Jung:** Like date field.

**Harim Jung:** Event date even.

**상대방:** This one you know that you know it is Hits map.

**Harim Jung:** Not only for the heat map especially for the stolen vehicle alert in analysis so do you remember previously we made a map chart in like a starting from which port and like we're different that is what like high level like Julia really like it but at some point Terry say like she want to show.

**Harim Jung:** A different ways.

**Harim Jung:** Because I remember what I remember is that because we remove the shape vehicle one like and I think that is more valuable here there so this for this one I think it's more like the distribute I remember you we also have another mat here but it's like.

**상대방:** Because I remember what I remember is that because we remove the shape one right and I think that is more valuable here.

**상대방:** There.

**상대방:** So for this one I think it is more like the distribute I remember you we also have another map here but it's like the.

**상대방:** More better I mean the map from using the police station location that that is also been my give us more information.

**Harim Jung:** From using the.

**Harim Jung:** Station that is also Granma gave us more information really sadly power bi especially my account our con map is pretty limited I tried all of single like a kind of like a way even using the data when D3 map is really hard to actually populate as good as like a tableau, you know so oh yeah so hard yeah commonal automatic this one might need actual code I think so.

**상대방:** Oh yeah right how the automatically recognized the Jimmy mentioned easily but this one might need actual code if you do not put.

**상대방:** Then we also have.

**Harim Jung:** Then we also have.

**Harim Jung:** Information for.

**상대방:** Information for the.

**Harim Jung:** The.

**상대방:** The postal code.

**Harim Jung:** Postal code.

**상대방:** For osi.

**Harim Jung:** Who is.

**Harim Jung:** Time.

**상대방:** Cod.

**Harim Jung:** Code.

**상대방:** E.

**Harim Jung:** As I say.

**상대방:** FSA code or yeah what code we have is that called fsa like the the first three digits of the.

**Harim Jung:** Or yeah what color we have is that called fxa like the the first three digit of the.

**Harim Jung:** Post code we have that from the maybe.

**상대방:** Post code we have that from the maybe lost location data.

**Harim Jung:** Loss location data might be if you can use those location data or we're going to have it we don't have a loose location in our bed because that is another plus but what we can do is that.

**상대방:** Might be if you can use location data or we don't have it we don't have a loose location in our member data because there is another loss but what we can do is that.

**상대방:** Our cpic data has.

**Harim Jung:** Our secret data has.

**상대방:** Location information and there is postal code on.

**Harim Jung:** Location information also.

**상대방:** It.

**Harim Jung:** Yeah just just for like just for your information like just simple example that you can see this one is actually we cannot use the map not only for like a loss even though we have a city name or I tried so many times but at some point I had prefer so if we have specific information in our database you know and there is.

**상대방:** Okay I have you so if you if we have specific information in our database you know and if there is.

**Harim Jung:** The.

**상대방:** The.

**Harim Jung:** City I.

**상대방:** Code I forgot to what is the code.

**Harim Jung:** Say if you have a call then I have a list called.

**상대방:** If we have a code then I have a list for the.

**Harim Jung:** The postal quality for those so we can join it okay yeah sure awesome that's really mostly mostly we could make it nice yes so we will follow the charts by please CPU or police post code right yeah yeah.

**상대방:** The postal code for those so you can join it.

**상대방:** Yeah I have a data in our sql server so I already know it.

**상대방:** Okay.

**상대방:** Mostly mostly we can map it.

**상대방:** So we will plot the charts by police city or police post code right.

**Harim Jung:** Okay so you mean young the city is not working in.

**상대방:** Okay so you mean the points the city is not working in the in the power bi.

**Harim Jung:** The power bi yes so most of like city and province is not working so normally my approach is using the yes.

**상대방:** Yeah that means that postal code is needed okay okay.

**Harim Jung:** So if we can actually map it out I think I can remove this one this is actually like very like duplicated like information if you can map it down yeah police agency and it's going to be okay yeah maybe better exactly and cross purpose rate is especially like orchest by Brian he want to see like a large is it from like a same province or like a cross province so this is actually the calculation we can tell and for instance based on the math for instance if we click on the like peel region or like throttle or some play some different.

**상대방:** Yeah.

**상대방:** Yeah maybe might be better than till.

**Harim Jung:** Like geographical filter then you can see the what actually what make is like a top stolen making here so stolen yeah simple we need more time to think yeah and one more thing is that.

**상대방:** So this one I think that we need to we need more time to see all the test and one more thing is that.

**Harim Jung:** Median or big career destiny yeah yeah and also another note from brian is that if possible we can add some real time top five or ten stolen makes or models from cpig add to this dashboard because for the existing dashboard that like reports that we.

**상대방:** Median or big career test not good.

**상대방:** You know.

**상대방:** The yeah and also another note from brian is that if possible if we can add some real time top five or ten stolen makes or models from cpig.

**상대방:** Add to this dashboard because for the existing dashboard that like reports that we distribute to the public is like yearly basis annual report right and this is more like a real time if we can use some cpik data.

**Harim Jung:** Distribute to the public is like not a yearly basis annual report right and this is more like a real time if we can use some CP data that I think that the tool open the information is not good.

**상대방:** For the solar vehicle that I think that too often the information is not good.

**상대방:** Okay yeah.

**Harim Jung:** So.

**Harim Jung:** I have just limited on the information only for the closing pair influence if you want to show the whole the future of the CP like the top 10 then there is the completely different project and the just for the purpose of this one and it is people I mean the if you see the top 10 there might be Toyota might be the first or something like that but this one close used for the fraud it might be different story.

**상대방:** Just limited the information only for the close impact if not if you want to show the whole the future of the CP like the top 10 then there is a completely different project and I just want to focus on this one and it is different I mean if you see the top 10 there might be toyota might be the first or something like that but this one close used for the fraud it might be different story.

**Harim Jung:** Okay so we will keep that in the years we'll remove the impact amount as well because that's also the impact from the use side right this is actually only from like a stolen in pick a month dimension they want to see the steps stolen and pick them all so that's why I decided to leave this delay in pectom on here.

**상대방:** Okay so we will keep at 8:8 or remove the impact amount as well because that's also the impact month from the community size right.

**상대방:** Here yeah I feel like for from different conversations they want different things okay it's fine then.

**Harim Jung:** Yeah I feel like we're from different colorations they want a different thing so this one very very hard to prioritize like what they want to see you know yeah so based on this stolen vehicle alert page what do we need to show is basically based on which region which city actually like has more like stolen l arthritis and per that city or region almost like top you know this vehicle was stolen and the price and how much actually.

**Harim Jung:** More like so this one is actually not showing how many podcasts frequently not in this sense this is the.

**상대방:** So this one is actually not showing how many podcasts are stolen most frequently not in this sense this is.

**상대방:** For the fraud misused as a fraud.

**Harim Jung:** For the frontiers has fraud.

**Harim Jung:** I see they might be a lot of stolen cars we are not telling about that information we are focusing on the frauds what case used for fraud in this case yeah so our intercessor liberty from just a simple information so yeah.

**상대방:** Might be a lot of stolen cars we are not telling about that information we are focusing on the fraud.

**상대방:** Yes what case used for fraud in this case yeah so the interest is a liberty from from just a simple information so yeah.

**상대방:** Yeah so that's the reason why sometimes I feel like if we use cpig in the title it's kind of misleading or maybe misleading that's what I'm saying.

**Harim Jung:** Yeah so that's the reason why sometimes I feel like if we use CP in the title it's kind of misleading or yeah it's a different way.

**상대방:** Yeah make it think different way yeah.

**상대방:** And also regarding just like small feedback regarding the like format is that possible that we put the score as just like zero decimal it's like an integer and also for the amount can we just like add a dollar sign this is just minor minor changes later that we need to just make the format is better.

**Harim Jung:** And also regardless like small feed time regarding the like format is that possible that we put the score as just like a zero testimony and also through their own mom can we just like add this is just a minor.

**Harim Jung:** Hundreds later that we need to just make the format it is better definitely no right everything should be updated I just like put I didn't actually put any like detail for like visual things I just want to check the server I understand so stolen the cool page I am a bit still confused like what kind of information we need to actually show and focus on the data field yeah case note as well we need to think yeah.

**상대방:** Yeah this one is where we need time to sink it again.

**상대방:** Okay we just refreshed our idea and just focus on what we were trying to show and after that we need to think it again yeah yeah and and also regarding the cross province rate.

**Harim Jung:** We just refreshed our idea yeah and just focus on what we will try to show yeah and after that no we need to start thinking again and also regarding the cross privacy which have expect the report province versus the first party prowess from the UI so how we connect these two programs used.

**상대방:** What the cross province that we have it's like the report province versus the first party pro wins from the UI so how we connect these two which programs we used.

**Harim Jung:** This is a very straightforward and simple as long as like requested they want to see is it actually like like.

**Harim Jung:** There's a column for the lost province and like a police prevalence right they want to.

**Harim Jung:** See if they're in the same like prevalence or not you know so which means alert started but like a police report they had different program.

**Harim Jung:** I wonder how it could happen so it's like lost location is where the.

**상대방:** I wonder how it could happen so it's like lost lost location is where the.

**상대방:** You also do have any background on this like why they introduce like who interested in this like they want to see what what kind of information they want to see it's like the location that they reported to the.

**Harim Jung:** They also do have any background on this like why they introduce like interested in this like they want to see what what kind of information they want to see it's like the location that they report into the.

**상대방:** Insurance company is different.

**Harim Jung:** Insurance company is different.

**상대방:** From the police agency that report they report it to.

**Harim Jung:** From the police agency that they report it.

**Harim Jung:** To yeah if if you have.

**상대방:** Yeah if if we have.

**Harim Jung:** The peak information and policy information and we have the quick location code right so in that case we have to provide and we can compare it with stolen palace we can compare it but I have a little bit of confusion here is that we are handling the fraud for the lot that means that.

**상대방:** The picker information and the policy information then we have the peak location code right so in that case we have a province there.

**상대방:** And we can compare it with the loss and the stolen province we can compare it but I have a little bit of confusion here is that we are handling the fraud a lot.

**상대방:** That means that.

**Harim Jung:** That means the current beaker location call.

**상대방:** Means the current peaker location code.

**상대방:** That should be compared current pick location code.

**Harim Jung:** S to be compared current picker location code.

**Harim Jung:** Versus.

**상대방:** Versus.

**Harim Jung:** Close location.

**상대방:** Close location cod.

**Harim Jung:** Call.

**상대방:** E.

**Harim Jung:** So.

**상대방:** So it is a little bit dentist is not now like raw and correct but like it's just like maybe we need to better think about what the how we define the cross yeah so based upon the interest the definition can be changed so we need to ask the brain that what he really want to see they might be better if not we might have multiple version of the cost yes.

**Harim Jung:** This is not now like raw correct but like it's just like maybe we need to better think about what how we define the cross so they put the interest the definition can be changed so we need to ask the bride that what do you really want to see they might be better proportion of the cost yes.

**Harim Jung:** Nice thing what about we remove it for now it was the completion yes.

**상대방:** What about we remove it for now maybe just like to realize yeah because he was a confusion yeah yeah it's confused yeah.

**Harim Jung:** So this one is sort of same ideas same prevents cross preference we can actually remove it right it's based on the cross rate as well yeah.

**Harim Jung:** I see and yeah this is going to be a reproductive by the map so I will just say name it as okay wait a.

**상대방:** At the same time I just check the no as well just to make sure we don't need that.

**Harim Jung:** Second I just check the nose has well just that way sure we do that.

**상대방:** I think for now.

**Harim Jung:** I think.

**Harim Jung:** For.

**Harim Jung:** Now.

**Harim Jung:** Oh is there any.

**상대방:** Oh is there any.

**상대방:** Tab that we need to discuss where this is all Harim.

**Harim Jung:** Tab that we need to discuss where this is all the there's another tab we need to discuss yeah if if we can actually so this is actually quite.

**상대방:** Okay.

**Harim Jung:** Interesting one because especially for the the tedious part they really want to check like not specifically ROI but they want to think about and want to see about like based on the.

**Harim Jung:** Money wise like have you actually saved the money that's what they want to actually check.

**Harim Jung:** Remember.

**Harim Jung:** Say yes so for instance about this one so for instance like I just put them like a net loss but oh sorry about this number just like forget about it's okay I mean this is not a solenoid this is actually I even don't know how can I put this title actually.

**상대방:** So tighter title is okay I mean the what's the range of.

**상대방:** This.

**상대방:** Whole.

**Harim Jung:** Because I cannot put it like a program performance at our you know from my end so I just want to discuss with you especially with so this is for all close impact right yeah yeah okay yeah so just long story short they want to see like based on the net based on the like a like alert they they should actually like pay this one 3.2 million but actually they what they actually paid essentially 1.0 million.

**상대방:** Closing path right.

**상대방:** Okay.

**Harim Jung:** So they could save lots of money that it's like originally the scenario is supposed to actually say but I'm not sure this is the right approach or not and totally in fact this is the same things that we mentioned from the first page you know and I'm not sure we can actually talk about like climate cost cleaning here so maybe red or remove it and this is mostly financial trend this same like a total impact but some of like total pain only the different is like a total impact and total pay is like different number why is neck loss this is.

**상대방:** Well what is net loss.

**Harim Jung:** This is the same one.

**상대방:** You know that you need to know the this one is that this is a lot but close impact.

**Harim Jung:** You know then you need to yeah this is the a lot but the close impact yeah that means that we already recognized this fraud that means that we declare in the claim so we can adjust a little more so the number in our claim side that members have already reflected our action so that does not show the exercise of the loss so one thing we can see is the avoidance value that is the one we can guess so we don't need to do subscription yeah here yeah the value that the input they are right yeah this oral actually like like replicated mostly from here if we only put.

**상대방:** That means that we already recognized this fraud that means we decline the claim so we paid just a little amount so the number in our claim side 10 numbers are already reflected our action.

**상대방:** So that does not show the exercise of the loss so one thing we can see is the avoidance value that is the one we can guess.

**상대방:** So we no need to do some substructure yeah here yeah because the value that the input they are ready.

**상대방:** Yeah reflected yeah right so modern spend has meaning in it is in this case.

**Harim Jung:** Some for instance if you only like some sum of like real total paid and everything is going to be the same so maybe no need to shoulders page.

**Harim Jung:** Yeah it really is the whole area is over here show some more detail inside then this might this pain might have some meaning so just just simply I want to ask you also again so do we like doing especially are we okay to show like a total paid amount.

**상대방:** Yeah it will be over there over here but if you want to show some more detail deep inside then this might this paper might have some meaning so.

**상대방:** I think we we don't need to show it reasons one is that the total pay it can be different across the members again or like they use different method to capture those.

**Harim Jung:** I think when we don't need to show reasons why is that the total pay can be different across the or like different measure to capture those so sometimes the amount that is played the paid mod is now to reflect the final one because it's okay I see I think this page is like yeah like more like a duplication and like too much information so yeah I think just like yeah I would suggest maybe we can just put it like into a parking lot and then we can think later so for now I think the one that we have discussed is great and then we maybe can add more insights more like to show like to tell story right just to first storytelling what kind of information that we can incorporate here and yeah and also I think based on the timeline if we can maybe finalize this like this page let's say or like the first two page this week and then maybe next week if we have bandwidth we can think about maybe we can add some more you know like generation status even though we can just discuss later but if if we have time I think it's also valuable to see to add some new life from the over volume qualified investigation cost with impact because I think that's also an important and mean well because the existing two page I think we kind of has limited information to show here.

**상대방:** So yeah so sometimes the like amount that displayed the amount is now to reflect the final one this kind of is avoidance is okay but just pay this next.

**상대방:** Yeah I would suggest maybe we can just put it like part put it into the parking lot and then we can think later so for now I think the one that we have discussed is great and then we maybe we can add more insights or like to show like to tell story right just to first start retelling what kind of information that we can incorporate here and yeah and also I think based on the timeline if we can maybe finalize this work like this page let's say or like the first two page this week and then maybe next week if we have bandwidth we can think about maybe we can add some large you know like generation status if not you can just discuss later but if if we have time I think it's also valuable to see them to add some you know like full funnel wheel from the new alert volume qualified investigation close with impact because I think that's also important and meanwhile because the existing two page I think we kind of has limited information to show here.

**Harim Jung:** Right here then I will I'm writing down a lot like notes we share together with this meeting I will share it right after the meeting and then we also talk about like data things right so I will change the data field to the event date right now and Jung could you possibly like support me for the cold like police code one that I can work on the data yeah.

**상대방:** Right.

**Harim Jung:** In the value join the city you need to add the code right or I could yeah and I said with the lady of the table and you might actually have this some minor but anyway.

**상대방:** When we join the cpit you need to add the code right so or I could write or I could and I said the table and landing of the table so you can join in and it might actually everything but some might not be joined but anyway yeah.

**Harim Jung:** And also regarding the date export from the.

**상대방:** And also regarding the date explored from the.

**상대방:** Website do you need me to redo that again today or maybe later because the close investigation that we upload to the base to the database is kind of outdated.

**Harim Jung:** Website do you need me to redo that again today or maybe later because the close investigation then outdated.

**Harim Jung:** So last time what I did is pour from them.

**상대방:** So last last time what I did is pour from.

**Harim Jung:** The eqs as platform was April or May but now it's already July so I wonder if you need to read them again to refresh the export from the database like from the platform you can turn then that is okay but if it doesn't take long then you do the drug depression but you have a timer in the simple server right.

**상대방:** The the eqs platform was April or May but now it's already July so I wonder if you need me to redo that again.

**상대방:** To refresh the export from the data like from the platform you take time then that is okay but if it does take long then you do not refresh it but you have a table in the sql server right.

**상대방:** You have you have a quality in sickle cell joining all of those here then just updated might be easy right.

**Harim Jung:** You have you have a quad in the separate post yeah then just obtain it might be easy.

**Harim Jung:** Right yes so that's what I'm thinking that we can do so that we can market as to like yeah July 20th I make a refresh maybe by the end of the august we can refresh again so that we can use the July end data as a cutout yeah so let's use to end of July as they call off because based on the time right yeah yeah so for now I just should I refresh or just wait yeah fresh okay yes just let me know when you refresh it so I will work on the data immediately yeah.

**상대방:** Yes so that's what I'm thinking that we can do so that we can market less July yeah July 20 let's make a refresh maybe by the end of the august we can refresh again so that you know I can then we can use the July end data as as a cut off pursuing my Have more data so it might be better yeah so let's use to end of July as a death call off because based on the time right.

**상대방:** Yeah so for now I just should I.

**상대방:** Refresh or just okay refresh okay?

**상대방:** No problem I'll do that.

**상대방:** Okay sounds good.

**Harim Jung:** Sounds good sounds good okay.

**상대방:** Okay.

**상대방:** Okay thank you and then maybe in the Wednesday I want we need to meet right there might be better Wednesday afternoon.

**Harim Jung:** Thank you and then maybe in the Wednesday I want to wait a little bit right yeah Wednesday yeah yeah maybe at the time until the time when I look through it again and then just think how we detect more but we are trying to show those pages yeah they're regarding the meeting with Julia and what you guys do would be comfortable to meet with you and maybe Thursday once we got there we also need to date yeah okay so what about okay Thursday I would say that with cold okay yeah and also our meeting on Wednesday maybe we can meet a little bit early yeah like on the morning slots so I can redevelop okay yeah okay I'll let me just set up the meeting now okay so for three of us is the just think okay unless they worry right yeah.

**상대방:** Yeah maybe at the time until the time I'm going to look through it again and then just think out what we need to add more or what we are trying to show those pages.

**상대방:** Okay.

**상대방:** There regarding the meeting with Julia what you guys do would be comfortable to meet with you and maybe Thursday once we have that we also need to yeah to we align the information and the date after then yeah so what about so.

**상대방:** Yeah okay Thursday afternoon I said I would call a mosque okay.

**상대방:** Yeah right yeah so maybe morning might be okay I'll let me just set up the meeting now just in case so for three of us is the just for thing okay.

**상대방:** On Wednesday morning right.

**상대방:** Wednesday morning yeah let me check the calendar same morning what's the morning what about 10 10 a.m yeah good okay to that not just that put it in to one hour in case we need that time and we can iterative if needed okay so this is for of us and then we I have another one with Julia for Thursday afternoon yeah okay.

**Harim Jung:** Calendar was in the morning what about 10 a.m yeah good okay.

**Harim Jung:** That just put it in to one hour in case we need that time and we can deliver if needed okay so this is for of us and then I have another one.

**Harim Jung:** With Julia for Thursday afternoon.

**Harim Jung:** All right thank you.

**Harim Jung:** Okay thank you.

**상대방:** Thank you good day.
