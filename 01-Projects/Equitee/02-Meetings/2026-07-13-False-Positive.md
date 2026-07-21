---
date: 2026-07-13
title: "False Positive"
granola_id: not_eTTonbvkmPoMGg
project: Equitee
type: meeting-transcript
tags: [meeting, granola, equitee]
source: granola
status: active
due: ""
priority: med
---

# False Positive

**Date:** 2026-07-13
**Project:** Equitee
**Owner:** Harim Jung
**Attendees:** Harim Jung
**Source:** Granola (공식 API, AI 미사용 자동 동기화)

## AI 요약 (Granola)

### False Positive Detection: Current Status

-   Extracted 1,000+ records; data and table now available in SQL Server for analysis
-   Corner extracted all PDFs; history loaded into a chronic response table per speaker
-   ~100+ alerts manually reviewed; 20–30% flagged manually (especially closed investigations)
-   AI-generated flags also in place: two-flag system (comment-based + AI)
-   10 flag categories defined; AI-categorized from comments, so not 100% accurate
    -   Standard definitions documented in a shared link for consistency between Corner and Harim

### Data Quality Issues

-   Policy date accuracy: cancellation dates sometimes off by more than a month
-   Duplicate periods exist in the history; combined to avoid interfering with decisions
-   Coverage information not available in the current database
    -   Only triggered claim coverage is retained, not original policy coverage
    -   This limits ability to determine whether a claim should have been covered
-   More accurate data may eventually be needed from the Dash or IP Stat

### False Positive Patterns Found

-   One confirmed pattern: before/after insurance from the same insurer, policy still active
    -   CVSA information flagged as completely incorrect in these cases
-   Export false positive example: coverage exported but policy still active at same company
-   Next step: review cases where response variable is already marked as false positive, then identify patterns
-   Goal: build an algorithm to identify false positives; gray areas expected

### Investigator Engagement Strategy

-   No current scenario for detecting false positives; pattern research is the first step
-   Suggested approach: mark target cases in the access sheet, note questions for investigators
    -   Identify insurers/members tied to those cases; find relevant contacts
    -   Internal team mainly uses network alerts; claim/policy alerts better suited to external investigators (e.g., TDI, Intact super users)
-   Check with Dominique on who is actively using EQ Insights
-   Acceptance working group feedback on scenarios can be shared
-   Intact likely has the most cases; Aviva expected to have fewer false positives

### Next Steps

-   **Summarize first findings and share by email**
    
    Capture early false positive patterns and insights discovered so far.
    
-   **Build a target case list with investigator questions**
    
    Mark cases in the access sheet, identify member/insurer breakdown, and flag what input is needed from investigators.
    
-   **Talk to Angel about investigator engagement**
    
    First question she'll ask: which members to engage; have the target list and member split ready first.
    
-   **Create a dimension/categorization table for false positive flag types**
    
    Adds clarity to the 10 AI-generated categories for shared use.
    

---

Chat with meeting transcript: [https://notes.granola.ai/t/fc85a6d8-f547-48c8-93b6-82576354cdd7](https://notes.granola.ai/t/fc85a6d8-f547-48c8-93b6-82576354cdd7)

## Transcript

**상대방:** And good morning everyone.

**Harim Jung:** Good morning everyone.

**상대방:** So did you have a vacation or is it good to some chip.

**Harim Jung:** So did you have a vacation or is it equal to send chip.

**상대방:** Yes it was I would say it was a combination of vacation and hockey tournament.

**Harim Jung:** Yes it was I would say it was a combination of vacation and hockey tournament.

**상대방:** Okay wow.

**Harim Jung:** Okay well.

**상대방:** Guys where where are your cameras I don't I cannot see you okay.

**Harim Jung:** Guys where are your cameras I cannot see you okay.

**상대방:** Yeah just my cheek is so old because I just got my wrist with two expressions so I'll get my camera off to recover okay okay okay okay and when when does your noise starts today what time is it okay now.

**Harim Jung:** Just a hand up my sheet is not so low because I just get my scratches so I'll get my camera off to recover.

**Harim Jung:** Okay okay.

**Harim Jung:** Okay okay.

**Harim Jung:** And when when does your noise starts today?

**Harim Jung:** Is it okay yeah I think sooner or later like the team so I might be totally muted.

**상대방:** Okay okay.

**Harim Jung:** I'm sorry yeah my building entirely we could cover like buildings is not working so we got total yeah like milk.

**Harim Jung:** Okay.

**상대방:** So let's start with the progress update young so like the guy did you update it provided update for the.

**Harim Jung:** So let's start with the progress update Jung so did you update it provided update for clearly.

**Harim Jung:** Those two slides for false positives.

**상대방:** Two slides for false positives.

**Harim Jung:** I'm not sure what you mean the we didn't create additional deck.

**상대방:** I'm not sure what you mean the we didn't create additional dec.

**상대방:** K oh no no yeah yeah so let me so just the what I asked to date update two slides because we need to share yeah I updated the one we extracted more than 1000 okay so.

**Harim Jung:** Yeah yeah so let so just the what I asked today to update the two slides because you need to share the one we extracted more social media fire okay so this okay so this was the was updated just checking if everything is up to date okay and for did you check the roadmap as well?

**상대방:** This okay so this was updated just checking if everything is up to date okay and for did you check the roadmap as well?

**상대방:** If any changes here.

**Harim Jung:** If any changes here.

**상대방:** It's okay.

**Harim Jung:** Okay yeah.

**상대방:** Okay yeah okay actually we create the table in the SQL server I mean the Harim did it and I also put all of the history into chronic response for each speaker yeah so put it into a table so so we can see all of the data source in one one value like as a chronic current history we can see all of them at once so it might be better to see what happens.

**Harim Jung:** Okay.

**Harim Jung:** Actually we create.

**Harim Jung:** The tab in the scrub server I mean the Harim did it and I also put all of the history into chronic risk for each speaker yeah so put it into a table so so we can see all of the data sourcing one one one bed like it's a critical history because all of them at once so it might be better to see the what happens.

**상대방:** Of course of course yeah thank you yeah and did corner extracted all the pdfs yeah files already all of them yeah all of them yeah yeah it's great progress yeah okay but we still have some issue in the accuracy of the policy information because that doesn't have accurate date for the data the pulse period so when the policy was cancelled in the middle of somewhere it does not show if set to date sometimes more than one more than a month difference from the actual cancellation date and dating the pedifier.

**Harim Jung:** Yeah and did corner extracted all the pdfs files already all of them yeah yeah it's great progress yeah okay but we still have some issue in the accuracy of the price information because that doesn't have accurate date for the post period.

**Harim Jung:** So and the policy was cancelled in the middle of somewhere it does not show you set date sometimes more than more than months difference from the actual cancellation date.

**Harim Jung:** And dating the PDF file.

**Harim Jung:** And also there are some duplicating the period so it was not equipped but I just tried to.

**상대방:** And and also there are some duplicating the period so it was not equipped but I just try to combine all of those in the history so sometimes that does not interfere our decision.

**Harim Jung:** Combine a lot of doors in the history so sometimes that does not interfere our decision.

**상대방:** So we just start to use it but at some point we might need accurate data from the dash or the IP stat.

**Harim Jung:** We just start to use it but at some point we might need accurate data from the dash or the IP stack.

**Harim Jung:** Okay so great progress so the update like in general high level so we collected all the data.

**상대방:** Okay so great progress so the update like in general high level so we collected all the data and we do have a table available on SQL for further analysis right yeah.

**Harim Jung:** And we do have a table available on SQL for further analysis right yeah.

**Harim Jung:** So in the data we can see the quality information like this.

**상대방:** So in the data we can see the quality information like this.

**Harim Jung:** Okay let me read it through just a second.

**상대방:** Let me read it through just a second polishing.

**상대방:** Yeah so policy the data pillar is March 24 to February 25.

**Harim Jung:** Yeah so policy the data pillar is March 24 to prior 25.

**Harim Jung:** That period is the period in the insurance.

**상대방:** That period is the period issued so at the end it is cancer.

**Harim Jung:** So at the end it is cancer.

**상대방:** But the insured period is specified like this.

**Harim Jung:** But the insured period is specified like this.

**Harim Jung:** So this one and the claim mentioned post commission clay information and CPU in all cases.

**상대방:** So this one and the claim information the post information credit information and the CP information something like this so in all cases the pulse information in the inserted in the middle of the clinical history.

**Harim Jung:** Inserted in the middle of the.

**Harim Jung:** So what's the.

**상대방:** So what's the.

**상대방:** Like if you want to provide high level insights and first you know signals for improvement what how we should communicate it's still early to communicate anything so one insight from the information is the for example the covers exported but people to export at the export there is a policy is still there and the company same that means that export information is false.

**Harim Jung:** But if you want to provide high level insights and first you know signals for improvement how we should communicate it still early to communicate anything.

**Harim Jung:** So one insight from the information is that for example the covers exported but people to export and export there is a policy is still there and company same that means that export information is the force.

**Harim Jung:** Let's say this was it false positive.

**상대방:** Was it false positive.

**상대방:** Yeah false positive means that the information is not correct yeah I mean like the like this particular example this was a false positive right.

**Harim Jung:** Yeah force positive means that the information is not correct yeah I mean like this particular example this was a false positive right.

**상대방:** So I want to say example for like yeah the something that we like the reason why it was false positive.

**Harim Jung:** So I want to say example for like yeah something that we like the reason why it was false positive.

**Harim Jung:** I didn't check the actual case.

**상대방:** I didn't check the actual case I will show you some samples I'll check it okay yeah this is great yeah but it is different from what like this like how it's different from the scenarios that we already providing the alerts based on.

**Harim Jung:** I will show you some samples I check.

**Harim Jung:** Okay yeah this is great yeah but it is different from what like this like how it's different from the scenarios that we already providing the alerts based on.

**상대방:** Is it like different scenario or like additional analytics into it or it's the same?

**Harim Jung:** Is it like different scenario or like additional analytics into it or it's the same?

**상대방:** Yeah currently we don't have a scenario for detecting the false positive so with this information we're going to try to find the pattern in what case it is first positive so one each sample one in the case I found was that before and after the insurance is from the same insurer some insurance company but that is still effective.

**Harim Jung:** Yeah currently we don't have a scenario for detecting the false positive so we're going to try to find the pattern in a bad case it is force positive.

**Harim Jung:** So one gated sample one in the case I found was that before and after the insurance.

**Harim Jung:** Is from the same insurer some insurance company but that is still effective.

**상대방:** That means that the CVSA information is completely incorrect information.

**Harim Jung:** That means that the CVSA information is completely incorrect equation.

**Harim Jung:** Okay.

**상대방:** Okay so could you please like this first you know first findings can you please summarize it in one email and share it with me yeah it might take time we are still checking all of those sometimes after a lot to date the peak was recovered sometimes yeah that was also another one so you got to debut the case with.

**Harim Jung:** So it was like this first you know first findings can you please summarize it in one email and share it with me yeah it might take time we are still checking all those.

**Harim Jung:** After a lot to date the peak was recovered sometimes yeah that was also one of the ones so we got a debut.

**Harim Jung:** The case with.

**상대방:** The certain response like if already there is response variable is already the post positive for those case we're going to review the pattern in what case that was in post passive so in that way we're going to check the information pattern after then you know we need to create some algorithm how we can figure out it is for possible now so we have two flex one is that from the comment we can get this first pass on that second one is that we also create a flag using AI so that one we're going to use it as well.

**Harim Jung:** Certain response like if already there is the response variable is already post positive for those case we're gonna review the pattern in what case that was in post passive so in that way we're gonna check the information pattern after then yeah we need to create some algorithm how we can figure out it is sports possible now so we have two friends one is that from the comment we can get this is first passed or not second one is that we also create a flag using AI so that one we're going to use it as well.

**Harim Jung:** And in some case without even those we can see clearly we can say this post fasting.

**상대방:** And in some case without even those we can see clearly we can say it is post fasting.

**Harim Jung:** So yeah so from now on we need to more sorry but sorry the research what happened.

**상대방:** So yeah so from now on we need to more sorry bit sorry the research what happened in those cases.

**Harim Jung:** In those cases and J do have something to add yeah so the first thing regarding the flag is not purely on AI because we manually flag it as well so just a note on the au column flag here so for the especially for those false positives we review those and then mark it as false positive cases.

**상대방:** And do you have something to add?

**상대방:** Yeah so the first thing regarding the flag it's not purely on AI because we manually flag it as well so just a note on the au column flag here so for the especially for those false positives we review those and then mark it as false positive cases.

**Harim Jung:** And how many alerts like manual alert you investigated manually it's about 100 and more than 100 ish.

**상대방:** And how many alerts like manual alert you investigated manually it's about 100 and more than 100 ish.

**상대방:** So yeah at least.

**Harim Jung:** So yeah at least.

**Harim Jung:** Especially for those close investigations I manually investigate those because those ones are the investigators that take time to review right so for those closed investigations and manually review those flags.

**상대방:** Especially for those close investigations I manually investigate those because those ones are the investigators that take time to review right so for those closed investigations and manually review those flags.

**상대방:** Okay yeah so I would say out of maybe about 30 to 20 to 30% is like manual yeah it's great job.

**Harim Jung:** Yeah so I would say out of maybe about 30 to 20 to 30% is like manual yeah it's great you have great job.

**상대방:** And I believe how like I cannot imagine how much time it took corner 33 fold those pdfs as well right or like one by one okay yeah so another like comment here is regarding those once you like to see the false positive cases and if the policy information is useful I think you can also use the flag you know like you can select that false positive you know like category and the star from there and then to see if we have any piter but based on the column 80 here asking what can help can be helpful is regarding the coverage part because I noticed here there some like property damage or physical damage I'm not sure this if this is related to the coverage because one of the categories you're breaking up.

**Harim Jung:** And I believe how like I cannot imagine how much time it took corner 33 for those PDFs as well right or like one by one okay yeah so another like comment here is regarding those once in your life to see the false positive cases and if the policy information is useful I think you can also use the flag you know like you can select that false positive you know like category and start from there and then to see if we have any fighter but based on the column 80 here I think what can help can be helpful is regarding the coverage part because I noticed here there some like property damage or physical damage for this if this is related to the coverage because one of the breaking up.

**상대방:** Oh those informations from the yeah I think I had an issue with my internet so what do you just say about shank I.

**Harim Jung:** Those informations from the state yeah I think I had an issue with my internet so what did you just say about shank I.

**상대방:** Yeah so one column I have is that regarding the policy I think one of the information might be helpful is regarding the coverage because some of the like alerts what the car discarded because there is there was no coverage.

**Harim Jung:** Yeah so one comment I have is that regarding the policy I think one of the information might be helpful is regarding the coverage because some of the new like alerts what this guarding because there is there was no coverage.

**상대방:** On current claim.

**Harim Jung:** Currently yeah we needed information from the IDC because this one is quite limited information for the policy so actually we need coverage for the policy sometimes.

**상대방:** Yeah we needed information from the IBC dash because this one is quite limited information for the policy so actually we need coverage for the policy sometimes.

**Harim Jung:** So yeah so in general we don't have.

**상대방:** So yeah so in general we don't have coverage information as part of our database it's not available to us.

**Harim Jung:** Coverage information as part of our database it's not available to us.

**상대방:** Yes it's part of the data model for the coverage but now it's not a field that we use for the detection model.

**Harim Jung:** Yes it's part of the data model for the coverage but now it's not.

**Harim Jung:** A field that we use for the detection model.

**상대방:** Actually in policy record but we have claim that would only keep the triggered the clean coverage only.

**Harim Jung:** In the policy record but we have claim the court claim that would only keep the children the clean coverage only.

**상대방:** So we can tell the original coverage but if it is paid by insurance company that means that the coverage is in the part of the policy problem is that in case of the policy a lot since we don't have the exact coverage so that that can happen the trim set is that because we don't know the coverage of the policy so we can tell this is to be covered or not we can tear it down.

**Harim Jung:** So we can tell the original coverage but if we paid by insurance company that means that the cover is in the part of the policy problem is that in case of the policy or not since we don't have the exact coverage so that that can happen.

**Harim Jung:** The dream set is that because we don't know the coverage of the policy so what we can attire this is to be covered or not working entirely.

**상대방:** Okay and how many flags how many categories you have 10.

**Harim Jung:** Okay and how many flags how many categories you have.

**상대방:** Category.

**Harim Jung:** Category.

**Harim Jung:** Can yeah okay.

**상대방:** 10 yeah here we can see the all of black.

**Harim Jung:** See the whole of plaques.

**Harim Jung:** Like this.

**상대방:** This.

**Harim Jung:** One is.

**상대방:** One is not.

**Harim Jung:** Not 100% because we used AI to categorize the based upon the comment.

**상대방:** 100% accurate because we used AI to categorize the based upon the comment.

**상대방:** So this is just just population yeah.

**Harim Jung:** So this is just population.

**상대방:** Yeah and it's something also worth to create a dimension right on yeah it's for clarity for.

**Harim Jung:** Yeah and it's something also worth to create this dimension right.

**Harim Jung:** For clarity.

**상대방:** So I would say it's like a different those flags we can.

**Harim Jung:** I would say it's like a different those flaps we can.

**상대방:** Like for this flags we have yeah name it like a different scenarios right basically for false positives yeah.

**Harim Jung:** Like produce flags we have yeah name it like a different scenarios right basically for false positives yeah.

**상대방:** Yeah it's it's great so anything found any insight there if you can record here then we also can summarize what those and create category some categorization for the information.

**Harim Jung:** It's great so anything found any insight if you can record here then we also can summarize one of those and create category some categorization for the formation.

**Harim Jung:** Okay great so what is the next step.

**상대방:** Okay great so what is the next step.

**상대방:** So just the analysis like all the comments and findings or anything else is spending here.

**Harim Jung:** So just the analysis and all the comments and findings or anything else is painting here.

**상대방:** Maybe maybe we need to focus on.

**Harim Jung:** Maybe maybe we need to focus on.

**Harim Jung:** This information they try to figure out how to pass towards identified they might be the first one.

**상대방:** This information they try to figure out how the post pass to us identified they might be the first one and I'm also trying to create some illustrator for analyzer for the dose information in one map one cryptically.

**Harim Jung:** And I'm also trying to create some illustrator in a rice for those information in one map.

**상대방:** Critical analysis photos information the after then we're going to try to.

**Harim Jung:** Analysis photos after then we're gonna try to.

**상대방:** More concrete information with investigators for the algorithm how to identify the first part team and there might be some gray area right how would you suggest to approach this should we start talking about it with the who is this dominion Dominic schem.

**Harim Jung:** More concrete information with investigators for the algorithm how to identify the false positive and there might be some gray area right support yeah how would you suggest to approaches should we start talking about it with the who is this dominique came.

**상대방:** E yeah.

**Harim Jung:** Yeah.

**Harim Jung:** We extend.

**상대방:** We still the do you have any contact with investigation team who is the contact point is Gran.

**Harim Jung:** The swing do you have any contact with investigation team who is the contact point is Gran.

**Harim Jung:** Or yeah I think I would suggest checking with dominate because I'm not sure who is actively using the EQ insights especially but I think from the internal they didn't use claim and policy alerts they use the network alerts a lot from internal team but for claim and policy I think the best way to you know like communicate with the investigators is for the external from the external like you know like TDI or if that any super user.

**상대방:** Or yeah I think I would suggest checking with dominate because I'm not sure who is actively using the eq insights especially then but I think from the internal they didn't use claim and policy alerts they use the network alerts a lot from internal team but for a claim and policy I think the best way to you know like communicate with the investigators is for the external from the external like you know like TDI or intact any super user from from the members so that when you'll know when they look at these scenarios what information they will look into and also what I can share is some feedbacks from our acceptance working group because they also provide some feedbacks for the scenarios I can share with you.

**Harim Jung:** From from the members so that you'll know when they look at these scenarios what information they will look into and also what I can share is some feedbacks from our acceptance working group because they also provide some feedbacks for the scenarios I can share with you.

**상대방:** Yes let me maybe talk to angel so when do you think you have when it's will be a right time to start.

**Harim Jung:** Yes let me maybe talk to angel when do you think you have when it's will be a right time to start.

**Harim Jung:** Talking with the investigators when you have some like what you like are you going to have the list of policies or claims to discuss so like how how would you like suggest approach these discussions what should be shared with the investigators and what kind of input we are looking for back.

**상대방:** Talking with the investigators when you have some like like what you like are you going to have the list of policies or claims to discuss so like how how would you like suggest to approach these discussions what should be shared with the investigators and what kind of input we are looking for back.

**Harim Jung:** To listing satisfy one we are investigating the target data is in this access sheet so maybe we can mark it here and then we also mark what point we need to check what information we might need from the investigators.

**상대방:** To list this it is fine I mean all of the all of the one we are investigating the target data using this access sheet so maybe we can mark it here and then we also mark what point we need to check what information we might need from the investigators so based upon this using this file we can mark it put a target one we need to discuss and the questions we need to ask and then we can add it and we can invest scatter with those items.

**Harim Jung:** So.

**상대방:** So yeah once you have this investigated accounts we would need to know the insurers right the members.

**상대방:** Because they they're not going to search across like 100 claims to confirm right.

**상대방:** So like claims or policies so we should think about the strategy right we can also find relate the insurer.

**상대방:** Because we have a lot of ID so we can have the insurer and we also can find.

**상대방:** The person in that company and we also have information about what that person so but also list.

**상대방:** We can contact.

**상대방:** The person who involved in those cases.

**상대방:** Okay okay so when you have that list ready so let's let's have a discussion how like what would be the next steps for us?

**상대방:** Okay.

**상대방:** And I will in the meantime I will talk to angel to ask her because like angio the first question she will ask and who is the member or who are the members that we want to engage right to talk about the claims and policies.

**상대방:** So what's the percentage of all the investigated you know counts ideas what's the percentage.

**상대방:** As like the split between a members.

**상대방:** If you know.

**상대방:** Once we select the target then we can see how many cases are from this member this member so maybe based upon that the student can contact those investigators yes yeah so let's like when we have that list ready right in the percentage so we will talk to like we will discuss the next step is okay okay good yeah I think from for the previously shipped vehicle assume day trading will have a lot of cases because a lot of you know like shift vehicle like ship from the port of montreal.

**상대방:** Okay.

**상대방:** The inter like of course like the biggest one right there in tact.

**상대방:** I think a viewer may have much less false positives right because they don't accept all the.

**Harim Jung:** They.

**상대방:** Alerts right.

**상대방:** This ink.

**상대방:** Yeah maybe I'll be personal 96 from a thousand in the third.

**상대방:** Yeah.

**상대방:** Okay.

**상대방:** Okay thanks team anything else to discuss.

**상대방:** Oh as it was in that one call is regarding the definition for those categories so we already documented in the ship link that I shared so that we have standard definition for each category because conno and I are both updating the flag so we have this document great and where is this on the.

**Harim Jung:** Don't.

**Harim Jung:** Like.

**Harim Jung:** Because.

**상대방:** Pda dashboard.

**상대방:** It's on the yes could I share a link to the.

**상대방:** Review it yeah I shared in the in this meeting chat.

**상대방:** Okay yes wait a second.

**상대방:** Yeah I said.

**상대방:** Yes I can see it okay I can also link this to our communication hub under this project yeah let's do it yeah.

**상대방:** Great again.

**상대방:** Let me just check if I have access to this I should but it's for some reason it's.

**상대방:** Still loading.

**상대방:** I think I have wishes with my internet or something it's imploding.

**상대방:** But I don't know if I won't be able to access it will let you know okay.

**상대방:** I got it so all good.

**상대방:** It just opened.

**상대방:** Okay thank you thank you very much okay talk to later by.

**Harim Jung:** Where are you right now?

**Harim Jung:** I am in Austin and my parents kitchen yes.

**Harim Jung:** Very hot and humid here I went running it was 20 I left 8 a.m. and went up 26 degrees outside in 84% humidity so I was very sweaty.

**Harim Jung:** And you're in where now Philadelphia right yes you're watching the Liberty bell.

**Harim Jung:** Watching that.

**Harim Jung:** Nice to see you nice to meet you nice to meet you.

**Harim Jung:** All right so I think you have you met with when Lou when Lou Harim out won the okay.

**Harim Jung:** So so when Lou is also consultant for us she's been with us for a long time she is.

**Harim Jung:** Like for the household energy team essentially so she works mainly on a black carbon project and fossil fuel tool which helps a bit with the sdg7 stuff and other household energy stuff.

**Harim Jung:** Well you know when Lou she's here to help like Alina's previous roles so it's facts and things.

**Harim Jung:** And she'll be working a bit she'll be working 25 time for salvatore as well.

**Harim Jung:** On health care facilitator electrification.

**Harim Jung:** So.

**Harim Jung:** I did just quick administrations I did just click through the approve on your contract Harim so it should be coming to the mail shortly you.

**Harim Jung:** Will you will learn very soon the bureaucracy challenges associated with doing anything at wh it can be a little cumbersome and time consuming so oh salvator join hello salvator I thought you would love it.

**Harim Jung:** Nice to meet you.

**Harim Jung:** Boom okay so this is kind of I know you don't have a whims account yet because you have not received a contract I'm assuming yet Harim because I just clicked it through so the wins account is your like wh email address and things like that and that will allow you to access we use Microsoft teams a lot and we have.

**Harim Jung:** A channel.

**Harim Jung:** I think that's the terminology for health and energy where we have basically the folders and things for the statistics that we've been working on this is where we keep the previous SG7 tracking progress reports the healthcare facility electrification database is there the household energy database there.

**Harim Jung:** And and etc.

**Harim Jung:** As soon as you get your WIMS account maybe when Lou if you're online you can help her figure out.

**Harim Jung:** I will add her as a member.

**Harim Jung:** Maybe you guys can have it probably towards the end of this week.

**Harim Jung:** Come through and you can help her show is that okay one lady thing.

**Harim Jung:** Yeah.

**Harim Jung:** Okay.

**Harim Jung:** So I'll make sure that you're a member as in the owner of that so this is where we keep everything there so I think that's one thing.

**Harim Jung:** So in that.

**Harim Jung:** Sense we also have.

**Harim Jung:** In that folder we'll have our previous consultants her name was Alina hand over notes where she gives kind of a current status of where.

**Harim Jung:** Current.

**Harim Jung:** Documents are.

**Harim Jung:** Such as we have.

**Harim Jung:** The databases themselves.

**Harim Jung:** Current so the way we do reporting at least for sdg7 and healthcare clean cooking we do.

**Harim Jung:** Reporting.

**Harim Jung:** In our global health observatory at the who so we have format for that and then we also put it in the format specifically for the scg7 tracking progress report.

**Harim Jung:** And then there's also the official SCG monitoring global UN format too so we'll have these different formats is basically country titles and pairing and for basically alliance you'll see all these different files.

**Harim Jung:** And formats so it would be good I guess to kind of.

**Harim Jung:** Look although it will be a little weird to you why would you do these things over and over again in a different format but that's just what we do.

**Harim Jung:** Also in there you will find we have an SOP because what we do for the sg7 monitoring one of the first tasks and for just the household energy and healthcare facility electrification monitoring is this notion of we have a standardized protocol to search publicly available surveys and data sets.

**Harim Jung:** So it would be I think that's probably the best thing to kick off on is to because that.

**Harim Jung:** S in terms of timeline it would be good for you to kind of work on both the database updating because essentially for the household energy we update the database through essentially the end of December then we get.

**Harim Jung:** It cleaned up as much as possible to run the statistical model in January for the official reporting.

**Harim Jung:** And then we'll get an official stop date typically at the end of December beginning of January like the database is closed we're not updating that one anymore so we so that length of time it's good to work on updating that one and it can be rather boring.

**Harim Jung:** So it's essentially looking for national healthhold surveys and we have all those protocol.

**Harim Jung:** So that and then you'll be also I think working on the healthcare facility electrification database I think just to vary your skill your time up a bit it'd be good to look at that SOP as well.

**Harim Jung:** And maybe evaluate a bit more and maybe salvator has some ideas but at least start looking at that first update for it because we would it would you know we.

**Harim Jung:** Haven't updated the HCF database what in three or four years salvator.

**Harim Jung:** Yeah that's okay if we're gonna do it so it'd be good if we can try to have some kind of at least initial cleanup or update of that, you know ideally maybe about four cop as I saw you know for example the clean air transition clean energy transition event so you put forward and these types of things so we can have maybe a little flyer at least with some updated stats.

**Harim Jung:** Initial preliminary estimates for the healthcare electrification by them as well.

**Harim Jung:** Also when you're looking at that SOP also be creative and if you have ideas how it can be adopted because healthcare facility electrification data is a bit tricky because indeed it's sparse.

**Harim Jung:** And definitely not collected in the same way not that household energy is that much better. But so you but I would say there's less coverage of healthcare facility electrification data.

**Harim Jung:** And ideally we want to get a better sense of what is this access level reliable versus just having any access at all.

**Harim Jung:** But the ultimate goal eventually, you know if we can get the, we would like to actually translate this to actually impact on care delivery, but that's something that is apply in the sky idea but something you could at least start thinking about in terms of population impact perhaps that's something that we worked on how to report and it would probably good I will give you a couple reports to kind of look at and get yourself up to speed too.

**Harim Jung:** This healthcare facility electrification we did try to estimate this population impacted by electricity access or not. And this was something we needed we had to basically end up doing some regional estimates.

**Harim Jung:** And pairing of different countries and stuff, but it'd be good because it goes into this kind of catchment population trying to estimate what that catchment population would be about healthcare facilities.

**Harim Jung:** So this is something so yeah some brand juices would be good there.

**Harim Jung:** So yeah check those SOPs out and then for the household energy is very much falling.

**Harim Jung:** For as a household liturgy it's really check the standardized data sets first which is like DHS which.

**Harim Jung:** Actually did just doesn't exist anymore so I don't know how much longer we're going to be doing that one.

**Harim Jung:** But the LSMS the MTF are you do you familiar with the MTF due to the multi ticking framework?

**Harim Jung:** And the World Bank? Yes.

**Harim Jung:** Yes so we should in theory get some data from there. We have some data sets from them but I don't think there's a publicly available however we work very very closely with the world bank so I can just say hey can you send it to us?

**Harim Jung:** We'll look there and then some of the other surveys is national census so that's where it gets a little dubious is you have to go through each of the countries and the national statistical website and try to extract data. And what's tricky is we have now added high income countries so that's something the SOP doesn't account for is it accounts for lmic's mainly.

**Harim Jung:** And in theory we need to be looking a little more high income countries as well but I would still prioritize LMIC first because that's the most important aspect. Salvatore where are you? I am in the wrong place.

**Harim Jung:** You're muted. You're muted. I can't hear you.

**Harim Jung:** I'm actually on a boat at this moment.

**Harim Jung:** Because I'm technically only like you and you can see outside.

**Harim Jung:** You understand how much we care about you not racial Europe.

**Harim Jung:** Nice to meet you.

**Harim Jung:** To join.

**Harim Jung:** That. Yeah, sorry go ahead.

**Harim Jung:** No, I think it's perfect. So yeah, I mean this is why we just don't.

**Harim Jung:** Yeah we don't want to make you just be sitting there for a couple weeks I think it would be good for you to kind of get used to adapted to some of the materials and get familiar. So yes we'll send you the health purposely electrification.

**Harim Jung:** Booklet. Well I'll give you links to the GHO and we just launched the sdg7 tracking progress report for this year. We basically write that clean cooking chapter every day every year. So we have to write the clicklet and you're going to do very involved and engaged in this. When Lou loves it.

**Harim Jung:** So anyway we will have these so it would have a look at those SDG7 tracking progress reports to see what you can have read through those.

**Harim Jung:** And ideally if you could even track what things have been done in the policy breach that would be great. I actually was very starting to avoid repetition.

**Harim Jung:** So within that regard this indeed will basically end of December January we'll run the statistical model with the University of Glasgow.

**Harim Jung:** And then we'll get the official estimates and we'll do country consultations so you'll help prepare the data to be sent to the regional commit the original economic commissions and then they're usually economic commissions will send it to the member state countries. They'll review and then if they have queries at a certain time frame to get back to us.

**Harim Jung:** And at the same time as this whole consultation process is going on we are working on drafting the chapters and other aspects. So that will basically be around February march ish is when we're drafting the policy sections this chapter.

**Harim Jung:** And then yes and then there's the whole communications cross production aspects that will go along.

**Harim Jung:** And yes, we just have an update to the statistical note this year so we have a new methodology basically to allocate for high income countries and we're now using GDP. Well, GNI in fact I think is covariate in estimates because we're now predicting high income countries and it helps there's actually.

**Harim Jung:** It's an important covariate to account for.

**Harim Jung:** And then we are looking at trying to eventually you know we had some amazing AI and some visuals that you were able to do so data visualization. So we would like to look and explore that a bit more for folks I guess the household energy and healthcare for sale electrification data I would think to have it a little more engaging and interactive.

**Harim Jung:** Because lots of people like to use our data and make their ultimate and then they get all the credit for giving our data with their shining bells and whistles when that's not part of it well it's hard work but not all the whole.

**Harim Jung:** And what else.

**Harim Jung:** Can I say.

**Harim Jung:** This moment.

**Harim Jung:** You're based how many what we're at time zone are you based in again? I'm in actual like ESC toronto like say I'm not going to yoga.

**Harim Jung:** Okay so you're six hours behind us.

**Harim Jung:** So great. So you'll be would you be able to start at 8:00 a.m. every day your time?

**Harim Jung:** Possible? No,

**Harim Jung:** Okay great then we'll have some overlap. There's a lot of challenges of working with.

**Harim Jung:** Yes. When Lou is happily in the US at the moment but then she's going to go to China soon so this will make it very difficult to have the overlap.

**Harim Jung:** But yes that is.

**Harim Jung:** Let's see anything.

**Harim Jung:** I just kind of just blew a bunch of stuff at you.

**Harim Jung:** Do you have any questions for me because I can, yeah, it's hard to do without a wins account. I can't do much for you at the moment. So I had hoped I assumed that it would have been done because this contract has been processed since May but apparently soon asked for it. Aspirational that we can no it's okay. I don't want to actually hear more of like a work and like data stuff but you're going to like cover so clearly. So I really appreciate this whole life cover.

**Harim Jung:** Brilliant. Okay so we'll send you some links and some undotserty salvatory.

**Harim Jung:** Yes nothing said that you gave up at you just want a couple of small point to fall.

**Harim Jung:** Any on the facility.

**Harim Jung:** One of the issues that we have had is the fact that the technician on the head of is not the same for everybody. Right. Some people, some organization consider that electricity has any board or reliable went and was known interaction for more than follow up in the previous two weeks or one week or if there was electricity to that moment or if there was research, it's quite inconsistent. This has been one of the challenges.

**Harim Jung:** So at the beginning of this war on the database we will very strict give also in terms of what is national representative. The problem is that we are too stricter then we are very little data.

**Harim Jung:** So one of the things that we were considering then is okay let's try to see what is available and circularify what these four beside by for this country. So at least we are not able to acquire. What does mean for this data and at least we try to feel a little more of the data paid but in parallel we build work with another one stream that we are starting right now so you are coming in the right moment and this is also very important.

**Harim Jung:** So it's really together with the gouache called lexa with the water segmentation.

**Harim Jung:** We are trying to do our work for consistency regarding your water sanitation, hygiene and electricity.

**Harim Jung:** This is something that we just started. I will forward you the email exchange and the concept knob. We are also creating an advice of organization. I would expect that for us we will be in touch with the classical units at World Bank UNDP etc. But the point is starting from what indicator exists.

**Harim Jung:** For electric reactions to water spa.

**Harim Jung:** Or the organization are considering electric availability, electricity at least things and then won't they consider as a source, as a backup source etc. So already doing.

**Harim Jung:** And of course I open and close one bracket where very closely we had in principle we are supposed to work remander 40 access of possibilities 60 on household but we will really play by the other. I mean whatever come out of root but let's say if you can if it's compatible would you go up consider already another few on mapping.

**Harim Jung:** What digital organization of software considerable what are the questions of global edition and then we will start working on it together with partners and already this opportunity to create some consistency among many organizations this will be fantastic. So I would say some daily education point of view.

**Harim Jung:** They do let's say.

**Harim Jung:** Short term.

**Harim Jung:** One data analysis gathering analysis second is what indicator I will show you the material.

**Harim Jung:** And then.

**Harim Jung:** I love.

**Harim Jung:** Them.

**Harim Jung:** It looks happy.

**Harim Jung:** Well as these sailing probably in six weeks.

**Harim Jung:** Yeah, he was just I think he's really expanding on this idea that indeed we struggle with the comparability across indicators in the healthcare facility electrification and you know we don't want the perfection of trying to get absolutely comfortable figures to limit the actual information and data coverage that we have on this and so we need to be creative in how we can have official kind of estimates that rely on very nationally representative data but also other ways of presenting data that approximate or can be done more at a local or regional level in terms of calibrating that and allocating that a bit more.

**Harim Jung:** And this kind of idea of being more creative with that and then with what partners and you will understand that data is a massive like competitive thing.

**Harim Jung:** Because data is gold right it's money.

**Harim Jung:** And we struggle sometimes and that.

**Harim Jung:** We do very rigorous data because we're very conservative in how we deal with these things but we want to make sure maintain our leadership and that to some extent and so we have to be careful that we have something very clear and put forward that we own in some sense before going to other partners because we want to make sure that it's wealth in some sense that this.

**Harim Jung:** I mean that we can follow what we do because that makes sense. I don't know. Linda, does that make sense? Did I explain that well not being totally a diplomatic but yes.

**Harim Jung:** I can be very idiomatic. Doing a good job of trying to do a diplomatic with them.

**Harim Jung:** And yes.

**Harim Jung:** Here's some more databases I put in the chat that scg7 that you'll be able to get the sdg7 progress reports on from the SDG7 website and you'll have the post reports too so maybe good to look at that.

**Harim Jung:** And then healthcare facility electrification report that's what else I need to give you.

**Harim Jung:** Maybe it's actually on wrestling that's why I do are we smart enough this now that would have been too much.

**Harim Jung:** Okay.

**Harim Jung:** In the chat too.

**Harim Jung:** Port and this was done with the world bank.

**Harim Jung:** And here it is the health difference electrification report that we created.

**Harim Jung:** This is what we the first time we created a global aggregate number putting it forward as an official estimate.

**Harim Jung:** Okay.

**Harim Jung:** So indeed I would keep going along and getting.

**Harim Jung:** Comfortable with these I would say once you get your wins account if you could spend a message or to either one loo or myself and say hey can you help me figure out what this stuff is?

**Harim Jung:** And it will just take you along a bit of time anyways to set up your account in any case.

**Harim Jung:** So we structurally we sit within a unit.

**Harim Jung:** That's also with the climate change team we used to stand alone there was a merger so we have this kind of SharePoint but we don't use a lot we're going to be shifting there more but we still kind of using our own specialized teams channels for the moment for sharing of documents and things like that.

**Harim Jung:** Yes.

**Harim Jung:** Anything else in forgetting one lou I think.

**Harim Jung:** Yeah I think you have covered pretty much everything just one thing I'm not sure if we should mention now just the household energy generic mailbox that's probably something takes a long time for you to monitor the data request and we have a template for sharing data this type of thing yeah we can discuss more in details when you have access.

**Harim Jung:** That was a very good point yes and we actually recently had issues with data sharing agreements because people are basically using our data and then selling our data for their own profits and we're not allowed to do that so we need to start selling the data sharing agreements and we do have this house with energy database so our house identity database is this input this is what you're updating right it's basically raw survey data we go mama go through the surveys take and extract our estimates using our own methods and put it in there and it's like 3,000 surveys.

**Harim Jung:** Strong and this is updated each year.

**Harim Jung:** And then that goes into the model but people will also like to so that household energy people want if you're in public institution and you're not as a nonprofit purpose we need to be sharing that data with the SWHO freely but we don't want to make it widely available on the website because then when I'll ask for it and we can't track the number of users needing it and we don't can track how it's being used.

**Harim Jung:** So we have this we do have this email that people can write to and seek the data and we have like I think five or six pending requests that we have low human capacity we even have a message saying like a short staff like you may take a while to get your response that was a good point when like you'll be best part of your task is to monitor that database, that email and respond to that but we'll discuss that because there's definitely some political nuance that will then go into tell that we'll have to discuss and we can discuss on it also on a case by case basis as you.

**Harim Jung:** Get.

**Harim Jung:** Up.

**Harim Jung:** To speed with these.

**Harim Jung:** As soon as you get that.

**Harim Jung:** Email etc.

**Harim Jung:** Let me know and I will make and I'll go ahead I try to add you now to the.

**Harim Jung:** Team's channel but if you don't have I'm not sure I'm going to be able to so I'm going to give you my.

**Harim Jung:** I am going to be offline I'm not going to be honest for a couple weeks but you can email me I have no problem with you emailing me in my personal email address or sending me a WhatsApp message on my personal WhatsApp I'm happy to get online real quick to to give you access once you get your whims account etc.

**Harim Jung:** I don't know if when there's going to be able to add you so I will try to add all I can get online add to it and answer questions and these things too and happy for a quick call I'm not going anywhere exciting I'm staying home.

**Harim Jung:** But home is nice to not have to work just now.

**Harim Jung:** Please feel free and yes when Lou knows how to get contact me was an amazing person and we love on the.

**Harim Jung:** So now embarrassing her but anyway so well okay there's so that's my my phone number personal please do not share this with other people like within the team is this is okay but like I have run in I have world bank people sometimes what's up in me and I'm like middle of the night I'm like what yeah but it's fine so personal.

**Harim Jung:** Close colleagues.

**Harim Jung:** Okay.

**Harim Jung:** All right any other questions.

**Harim Jung:** Now I'm really like happy like most of the things already cover like I will actually write down some notes see if I have like additional question and then like I said you're bad I will wait for like contract and everything so thank you so much especially you have there's really amazing no we're excited to have you and it's a very fun team to work on I have to say we are very comfortable I would say and casual with each other.

**Harim Jung:** So please yeah be aware that yes we're a fun team I would say I don't know but yeah anything okay well all right.

**Harim Jung:** Well I'm gonna.

**Harim Jung:** Go back my best friend is here with my parent at my parents house we're celebrating my mom and my best friend's birthday so we're gonna go back to see and hang out with them so thank you both bye.

**Harim Jung:** They're not oh yeah.

**Harim Jung:** My yummy will be my five to eating my.

**Harim Jung:** Own.

**Harim Jung:** Take.

**Harim Jung:** My.

**Harim Jung:** Iowa.

**Harim Jung:** Stuff.

**Harim Jung:** Going to get a very similar.

**Harim Jung:** Muscle.

**Harim Jung:** Hood.

**Harim Jung:** So I'm gonna get this to her schema.

**Harim Jung:** There's a nice.
