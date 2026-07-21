---
date: 2026-07-20
title: "Equite AI False Positive"
granola_id: not_CxmtJzAr0Kkt1E
project: Equitee
type: meeting-transcript
tags: [meeting, granola, equitee]
source: granola
status: active
due: ""
priority: med
---

# Equite AI False Positive

**Date:** 2026-07-20
**Project:** Equitee
**Owner:** Harim Jung
**Attendees:** Harim Jung
**Source:** Granola (공식 API, AI 미사용 자동 동기화)

## AI 요약 (Granola)

### Context and Background

- Meeting with a colleague to discuss Equite AI false positive analysis work
- External pressure: Viva meeting last Friday (Julia + VP of Fraud Crime) flagged concerns over high false positive rates and sentence rate in EQ Insights
  - Julia shared the AI initiative targeting false positive reduction
  - Committed to delivering initial results by September
- Scope confirmed: CBS and CP data only, not broader expansion

### False Positive Case Review

- Reviewing 471 alerts total; checking each one individually
- Two root causes of false positives identified:
  - Data source legacy issues (e.g., incorrect CP/CBSA data)
  - Business rule gaps (e.g., missing coverage checks, policy interpretation errors)
- Substate used to classify true positive vs. false positive
  - No-fraud substate categories include: data inconsistency, not suspicious, no coverage
  - Some no-fraud cases stem from insufficient info or incorrect scenario interpretation
- False positive join: master table already flags false positives; plan to add a new column rather than re-flag independently
  - Leverage existing flagging work rather than duplicating effort
- Sample sizes: 1,100 in main dataset; 471 additional alerts for latest vehicle model years (2001+)
- Most cases appear to be from Quebec; Quebec has no IBC data, limiting coverage detail

### Pattern Identification and AI Tooling

- Current patterns generated via ChatGPT/Copilot: mostly okay but not fully accurate or well-grouped
- Plan to switch to Claude Code for better pattern application to individual cases
- Pattern structure: propose adding category and subcategory columns
  - Existing granular groups become subcategories
  - New higher-level categories created above them
- AI preferred over Python scripts for pattern detection: faster, but requires manual review for accuracy
- Colleague will rearrange and regroup patterns this week if time allows

### Scope, Timeline, and Prioritization

- Risk of scope creep flagged: tackling all false positive reasons may miss the September deadline
- Agreed approach: prioritize the biggest issue first (likely CBSA/CP data credibility)
  - Note other reasons as found, but do not expand scope
  - Some issues (e.g., policy coverage gaps) cannot be resolved due to missing data
- Stolen car edge case noted: if a car shouldn’t be insured, coverage status is irrelevant
- Two-week target: complete individual case review and share categorized results

### Next Steps and Open Items

- Plan to align internally before scheduling a sync with Julia
- After patterns are confirmed, schedule interview with Desjardins super user (Jackie) to understand their false positive observations
- New PC/laptop upgrade still pending: both waiting on Julia’s approval; needed for running AI models faster
- Shipping/picker history work noted as good but lacks detail on overlapping policy periods and coverage codes

### Action Items

- **Regroup and reformat false positive patterns into category/subcategory structure**

  Use Claude Code to improve pattern accuracy; target completion this week so the team can review higher-level groupings.

- **Complete individual case review and share categorized results**

  Target: within two weeks; output should clarify which false positive cases fall into which root cause category.

- **Document patterns and flag logic in shared documentation**

  Add explanations for current patterns and how flags are assigned so the team can track progress going forward.

- **Schedule internal alignment meeting before syncing with Julia**

  Align on findings and scope internally first; then schedule a separate meeting with Julia once ready.

- **Schedule interview with Jackie (Desjardins super user)**

  Once patterns are confirmed, ask Jackie what she observes based on the alerts Desjardins receives.

---

Chat with meeting transcript: [https://notes.granola.ai/t/92090a75-a50c-4284-8424-d9a065c48f2a](https://notes.granola.ai/t/92090a75-a50c-4284-8424-d9a065c48f2a)

## Transcript

**상대방:** So how else you.

**상대방:** Can?

**상대방:** Watch the game?

**상대방:** S?

**상대방:** Oh, okay.

**상대방:** The final game, but I feel like it supports boring, to be honest. I'm not a fan of Argentina or Spaniard.

**Harim Jung:** The final game.

**Harim Jung:** I feel like it supports the opinions boring, to be honest.

**상대방:** Who won the game. Actually, I didn't see.

**Harim Jung:** I didn't see.

**상대방:** It. Oh, spain. Wow.

**Harim Jung:** It. Oh,

**상대방:** Great.

**상대방:** Yeah.

**상대방:** The players from are really young.

**Harim Jung:** Put the players from spin are really young.

**상대방:** Like they look young.

**Harim Jung:** They look young.

**상대방:** Like Jung is only 19 years old.

**Harim Jung:** Like Jung is only 19 years old. Yeah, they're pretty young. They have a really pretty young game.

**상대방:** Yeah, they're pretty young. They have a really pretty young game.

**상대방:** Like team.

**Harim Jung:** Compared to argentina.

**상대방:** Parents,

**Harim Jung:** Did you see your message, like, crying? He shared the tears. Yeah.

**상대방:** Yeah.

**상대방:** That's sad.

**Harim Jung:** That's that. Yeah, that's sad.

**상대방:** Already.

**상대방:** Yeah, but we can only have one winner, right? So it is.

**Harim Jung:** Yeah, but we can only have one winner, right? Exactly. It is.

**상대방:** Good. Yeah, actually I subscribed TSN.

**Harim Jung:** Good. Yeah. Actually, I subscribed TSN. I just.

**상대방:** But I just started a subscription after failing the quarantine. Yeah, because this.

**Harim Jung:** Started subscription after paying the quarantine.

**Harim Jung:** Yeah. Because this, like.

**상대방:** Time it takes longer, right? It's longer than one month, but usually the subscription is just for one month. So yeah, that makes sense.

**Harim Jung:** This time it takes longer, right? It's longer than one month, but usually there's the three places just for one month. So, yeah, that makes sense.

**상대방:** Yeah, good.

**Harim Jung:** Yeah.

**Harim Jung:** Good.

**상대방:** Hustle or dad, Jung saw. I remember you took some time off for the deck. How's that?

**Harim Jung:** Hope you're dead, young soul. Remember you think took some time off for the deck or stat? The fans were dead.

**상대방:** Defense or deck? Oh yeah.

**Harim Jung:** Oh, yeah.

**상대방:** Yeah, thanks.

**Harim Jung:** Yeah. That.

**상대방:** I fixed all of those and I'm still trying to do some more on our plant bed.

**Harim Jung:** Fixed all of those in the. I'm still trying to do some more on our plant bed.

**상대방:** Yeah, so I did some. And I also have a plan to create some small deck. There might be.

**Harim Jung:** Yeah. So I think the sun. And I also have a plan to create some small deck that might be.

**상대방:** Four pit and 10 pit size deck small tag. I'm going to try to build a rational one.

**Harim Jung:** Pulpit.

**Harim Jung:** And 10 pit size deck small diameter. I'm gonna try to put the original one.

**상대방:** So you didn't very big, right? It won't be a very big project because four times 10 feet, but 10 years long.

**Harim Jung:** They're not very big, right? It won't be a very big project because world times 10 feet. But 10 years more.

**상대방:** It's like a short long deck. Yeah, there used to be a little bit easy because I do not into the ground. I mean the subsurface is already in the stall, so it might be a little bit easier. But I need to design all of those and purchase material as well.

**Harim Jung:** It's like a short, long bag. Yeah. And it's really easy because I do not think it's the ground. I mean, the subspaces already in a store. So it might be a little bit easier.

**Harim Jung:** I need to design rule tools and purchase material as well.

**Harim Jung:** Yeah, I saw a message from you, Leah. She asked to schedule this meeting.

**상대방:** Message from you, Leah. She has to reschedule this meeting.

**상대방:** So I wonder maybe some might be need to discuss with you.

**Harim Jung:** So I wonder to discuss with this to you.

**Harim Jung:** Here.

**상대방:** And something we need to do internally. So maybe we have another meeting. Yeah, that's good. Yeah, that's what I think as well. Like we can discuss first before sharing anyways for because we need to like align internally first. Sometimes I feel like we are so different, but it's not like it's now wrong, but it's just like we did or like a line first before we stick with her. Yeah. So yeah, maybe you get what we can do is that we have separate meeting. So for us, for this meeting is only three of us, but maybe for the Julia to sync with Julia, we can just once we are ready, we schedule the meeting with her. So.

**Harim Jung:** And something we need to do internally. So maybe. Yeah, we can.

**Harim Jung:** Yeah, that's good. Yeah, that's what I think as well. Like, we can discuss first before sharing any thing with her because we need to, like, align internally first. Sometimes I feel like we all serve different. But it's not like it's now wrong, but it's just, like, within my first before we take away her. Yeah. So, yeah, baby, you get what we can do is that we have separate meeting. So for us, for this meeting, it's only history of us, but maybe for the ulia to sync with Julia, we can just. Once we are ready, we schedule meeting with her. So.

**상대방:** One thing I want you to remember is that we have a schedule. So as you see from our meeting.

**Harim Jung:** One thing I want to remember is that we have a schedule.

**Harim Jung:** So as you see from our meeting.

**상대방:** This might be the world latest scale we have the kick of documentation. If you go there.

**Harim Jung:** This map is the latest scan we have the documentation. If you go there.

**상대방:** July to September, we are to the process identification.

**Harim Jung:** The July to September to process identification.

**상대방:** There might be the one. So I think that you already started to do something. So one thing I want to share is that.

**Harim Jung:** And the back of the one. So I think that you already started to do something.

**Harim Jung:** So one thing I want to share is that.

**상대방:** I think you remember this one.

**Harim Jung:** I said to me, you remember this one?

**상대방:** The pattern.

**Harim Jung:** The pattern?

**상대방:** So did Connor have a review though? So now it's a celibate. Yes, trying to add more patterns.

**Harim Jung:** So this corner has a review. It's trying to add more patterns.

**상대방:** So he's doing this side so I could copy and this is a separate one, but I'm going to come back all of those maybe later.

**Harim Jung:** So he's doing this side. So I could copy. And this is a separate one, but I'm going to combine all of those maybe later.

**상대방:** So this one has, you have a response variable.

**Harim Jung:** So this one has response variable.

**상대방:** Response value from our workflow state.

**Harim Jung:** Response value from our workflow state.

**상대방:** Sub state.

**Harim Jung:** Sub state.

**상대방:** So that already have this is prod no fraud that information is already there.

**Harim Jung:** So they already have this is the prod, no fraud that information is already there.

**상대방:** And this is from.

**Harim Jung:** And this is from.

**상대방:** Past table from what the substate.

**Harim Jung:** Two positive front state.

**상대방:** And this non fraud from substate. Some of those we could get from the comment.

**Harim Jung:** And this law fraud from sofa skate. And some of those we put from the comment.

**상대방:** Also have some this data issue. This is postpartum. There's a comment on that. So based upon that. So according to the one I have.

**Harim Jung:** Also have some distance that I should pass to build comment on that. So based upon that. So according to the one I had.

**상대방:** To xyening out of doors.

**Harim Jung:** To zinch.

**상대방:** 471.

**Harim Jung:** 471.

**상대방:** 471 cases in the habit response.

**Harim Jung:** 71 cases in God were having his pass.

**상대방:** So I'm still checking each one.

**Harim Jung:** So I'm still checking each one.

**상대방:** Especially the one if you see the one. This is the hype through positive case.

**Harim Jung:** Especially the nucleus. This is.

**Harim Jung:** The high true positive case.

**상대방:** And this is as well.

**Harim Jung:** And this is as well.

**상대방:** And some of the cases so many false positive.

**Harim Jung:** And some of the cases, so many false positive.

**상대방:** Especially export and there is a claim that usually there is a post pass date, something like that. So multiple export mostly.

**Harim Jung:** And there is a this claim that usually.

**Harim Jung:** There's a porcelain, something like that. My temporary export mostly.

**상대방:** Most reports passed. So in that way. So in my case, if I click this one, I can see all the tests.

**Harim Jung:** Forced past. So in that way. So in my case, if I click this one that I can see multi-text.

**상대방:** So I'm checking those information with CGI and the CGI code says I claim.

**Harim Jung:** So I'm checking those information.

**Harim Jung:** With CGI and CGI core, the CCI claim.

**상대방:** Checking details. So I'm trying to summarize what happened there. So something like this.

**Harim Jung:** I'm checking details. So I'm trying to summarize what, what happened there. So something like this.

**Harim Jung:** Just a short memory. You've got police category.

**상대방:** Short memory for those for each category.

**상대방:** If I have something I got inside, then I can record it and then it's marked as made postpartum.

**Harim Jung:** If I have something.

**Harim Jung:** I got inside, then I can record it. And this market has made it to postpartum.

**상대방:** That way I'm trying to give you the cases as much as possible. So I strap that within two weeks. I'm going to review all of those.

**Harim Jung:** That way I'm trying to give you the cases as much as possible. So I've got that within two weeks. I'm going to give you all of those.

**상대방:** Then I give you more variety on what case you have to post positive to positive debt.

**Harim Jung:** And then I give you more, more better idea.

**Harim Jung:** What case you have to persuade?

**상대방:** So this isn't just my side. This is separate from the rings you're doing. So you can do a new weight and then you try to figure out the identification process and you can make a note on what we need to ask to the member company.

**Harim Jung:** So this isn't just my side. This is separate from the swing. So chewing, you can do a new weight and then, you know, try to figure out the identification process and you can make a note on what we need to ask to the member company.

**상대방:** I will do in that way. I will also mark a note on that. Then maybe in after two weeks probably. I want to work. We have a chance to talk with member.

**Harim Jung:** How to integrate. I've also marked, like, a note on that. Then maybe, maybe after two weeks, probably one, two, we have a chance to talk with member.

**상대방:** I think that you might have some good connect point.

**Harim Jung:** I think you might have some good connect at the point.

**상대방:** So that at the time we can ask it.

**Harim Jung:** So that at the time you can ask.

**상대방:** And make it more clear on what's happening there. So a few questions. Make sure for the column BCD where that flag comes from.

**Harim Jung:** And make a more clear on accepting.

**Harim Jung:** There. So a few questions. Make sure. Just understand. So for the column BCD, where that flag comes from. But this is from.

**상대방:** So this is from some state.

**상대방:** I use the substate.

**Harim Jung:** State.

**상대방:** If assisting of state did also have the true first to post fast.

**Harim Jung:** If it's a small state, it also have true past and postmaster tail.

**상대방:** There.

**상대방:** Are two positive is.

**Harim Jung:** The true positive is.

**상대방:** Which is like close with impact from.

**Harim Jung:** Which is like close with impact flood.

**Harim Jung:** Okay, I see. Makes sense. So there is no subset of.

**상대방:** AC makes sense. So there is no subset of false positive, right? Because it's just like no fraud. But we can first based on the current flag we can now tell the false positive. And then we need to join that to the table that I was working on to tell which one is.

**Harim Jung:** False positive. Right. Because no, it's just like no flawed. But we, we can for based on the current flight, we can now tell the false pocket. And then we need to join that to the.

**Harim Jung:** The table that I was working on to tell which one is.

**Harim Jung:** The.

**상대방:** The false positive.

**Harim Jung:** False positive.

**상대방:** Pract.

**상대방:** Ice. Yeah. So in the substate.

**Harim Jung:** Yeah. So in the soft state, we can.

**Harim Jung:** Choose certain people, we can this is false positive.

**상대방:** We can tell this is false positive.

**상대방:** And true positive. So is the column be the false positive?

**Harim Jung:** And true parsley. So is the, is the column be the false positive?

**상대방:** Oh you already joined back to the flag of the false positive.

**Harim Jung:** Oh, you already joined back to the flag of the false positive.

**Harim Jung:** Also had to break there.

**Harim Jung:** I'm confused. No, I didn't correct that. But we can, we can, we can centralize it, right? Because we have the master table and we already flag the false value because I, I don't want you because we have take put some time on that, right? I want leverage those information instead of we flag it as automatic and then we just put it here there and then already know how I did it.

**상대방:** No, I didn't correct that but we can we can we can centralize it right because we have the master table and we already flagged the false positive because I don't want you because we have take put some time on that right. I want leverage those information instead of we flag it as false positive and then we just put it here there and then do that. I will let you know how I did.

**상대방:** It.

**상대방:** Yeah okay so I'm going to mark it because this is from the service state. So it is a static does not with my personal opinion. I mean just I get it from the substate. So maybe in the our table I'm going to create one more column. So like yes that would be great. So I want refine also leverage what we have already did right so that we can.

**Harim Jung:** Yeah. Okay. So Harvard battery, because this is from the source state. So it is the static. There's not with my personal opinion. I mean, just from the substate.

**Harim Jung:** So maybe into our table, I mean, create one more color. So like, yes, that would be great. So I want refine and also language what we are right at it. Right. So that we can make it better.

**상대방:** Make it better.

**상대방:** So yeah in this case for example.

**Harim Jung:** So, yeah, in this case, for example.

**상대방:** No proud.

**Harim Jung:** No prod.

**Harim Jung:** Off.

**상대방:** And if you see the substate.

**Harim Jung:** And if you see the substrate.

**상대방:** From here.

**Harim Jung:** And see from here.

**상대방:** Substrate.

**상대방:** Like this.

**상대방:** Data variable inconsistency no fraud.

**Harim Jung:** Consistency.

**Harim Jung:** No fraud.

**상대방:** Not suspicious not suspicious.

**Harim Jung:** No substitutions, nurses teachers.

**상대방:** Okay.

**상대방:** Okay. Makes sense.

**Harim Jung:** Okay.

**상대방:** So only those cases.

**Harim Jung:** So only those cases.

**상대방:** This is.

**상대방:** Not for administrative sports.

**Harim Jung:** Not for the means that this is sports positive.

**상대방:** Day.

**상대방:** Information is not correct.

**Harim Jung:** Information is not correct.

**상대방:** Right.

**Harim Jung:** Right.

**상대방:** But sometimes the no fraud can be there's not enough information or the interpretation of the scenario is done correct or the there's no coverage right so there's a lot of.

**Harim Jung:** But sometimes the no fraud can be there's no, not enough information or the interpretation of the scenario is not correct or the there's no coverage, right? So there's a lot of.

**상대방:** Reasons or like some why we need to check one by one.

**Harim Jung:** Reasons or like somewhat we need to check one by one.

**상대방:** Yeah so for those cases if you see mostly that has a reason.

**Harim Jung:** Yeah. So for those cases, if you see mostly get acceleration, but yeah.

**Harim Jung:** So yeah, once we categorize this works fast, you can check one by one inside. Then mostly the now cover the kind of master very rare mostly.

**상대방:** Once we categorize data force first you can we can check one by one in inside then mostly the now cover is the kind of not very rare.

**상대방:** Mostly.

**Harim Jung:** But.

**Harim Jung:** Anyway, those, those information is not trigger the true past here. That means that this information is.

**상대방:** Those those information is not not does not trigger the true positive that means that this information.

**상대방:** Can be regarded as postmaster evaluator.

**Harim Jung:** Can be valued as possible.

**상대방:** Because this is positive right all of those are positive.

**Harim Jung:** Because this is positive, right? All of those are positive.

**상대방:** But not through positive.

**Harim Jung:** But not through plastic.

**상대방:** Then all of those.

**Harim Jung:** And all of those.

**Harim Jung:** First.

**상대방:** Positive.

**상대방:** Make sense?

**상대방:** Makes sense but how is there's two part to cause this false positive right one is because of the data source.

**Harim Jung:** Makes sense.

**Harim Jung:** But like there's too hard to cause this false positive, right? One is because of the data store.

**Harim Jung:** S.

**상대방:** Right the data source that has some legacy issue that caused this false positives another part it can be some business rule setting for instance we didn't check against the coverage or we didn't check other things so there are I think this this tool like combine those false positive and then we need to decide which part we need to focus on first yeah moving to the post of them other than through positive we need to take over those even though there is no the second part we cannot control our set yeah yeah but if you can have any symptom or indicator from the from the typical history and also we also can detect it.

**Harim Jung:** Right? The data source that has some legacy issue that caused these false positives. Another part, it can be some business rule setting. For instance, we didn't check against the coverage where we didn't check anything. So there are, I think this, this tool like combine those false positive and then we need to decide which part we need to focus on first.

**Harim Jung:** Yeah, move into a positive tab other than through positive. We needed to get all of those. Even though the second part we cannot control.

**Harim Jung:** Our set. Yeah, yeah. But you can have any symptom indicator from the story and also we also can detect.

**Harim Jung:** It.

**상대방:** This is not just the encrypt CP or incorrect CBSA not just we try to detect all of the reasons.

**Harim Jung:** Yeah, this is not just the incorrect.

**Harim Jung:** CP or incorrect spacing, not just.

**Harim Jung:** To try to detect all of the reasons.

**상대방:** We don't know but if it does not create true positive then the value was all to support it okay I have this question is because I'm a bit concerned about the scope and the timeline if we.

**Harim Jung:** We don't know, but if it does not create too positive, then we go to post passing.

**Harim Jung:** The reason why I have this question is because I'm a bit concerned about the scope and the timeline if we.

**상대방:** Keep like keep the expansion you know if we want to tackle all the.

**Harim Jung:** Keep like it's been keep the expansion. If we want to tackle all the.

**상대방:** Problems existing for these scenarios may not be able to hit the deadline the initial timeline that our our targets all very narrow just to CP and CVSA only.

**Harim Jung:** Existing for these scenarios, we may not be able to hit the deadline.

**Harim Jung:** The initial line that just CPA and CPSA only.

**상대방:** So the other reason it's not so huge.

**Harim Jung:** So the other reason is not so huge.

**상대방:** You know that other than maybe there might be some but you can you already define something like coverage is not there the there is one thing the other one so the other one might not be so not so many reasons.

**Harim Jung:** You know that other than maybe there might be some, but you can be already find something like code is not there. That is one thing. The other one. So due to one might not be so not so many reasons.

**상대방:** Yeah so what I suggest is that we select on repeat we select you like the the most.

**Harim Jung:** Yeah. So what I suggest is that we select our VP. We selected you like the.

**Harim Jung:** Most biggest part of the issue and then we solve it first.

**상대방:** Biggest part of the issue and then we solve it first.

**상대방:** Yeah.

**상대방:** Yeah so that is that's why I we can now tackle all the existing problems but maybe we can.

**Harim Jung:** Yes. So that is why we can now tackle all the existing problem.

**Harim Jung:** S, but maybe we can.

**상대방:** Select the most or like the highest priority one and then we we we tackle it first yeah maybe I think the one of the big reasons might be the CBSA and the CP data is not credible.

**Harim Jung:** Select the most or like the highest priority one. And then we tackle it first.

**Harim Jung:** You know, maybe I think one of the big reason the course might be CBSA and the CP data is not critical.

**상대방:** To a certain degree.

**Harim Jung:** To certain people.

**상대방:** So then below one.

**Harim Jung:** So then below one.

**상대방:** Definitely we're going to focus that one but even though there is correct that there might be another reason but then the another reason it's not so huge you know so that's one data and if you find any other reason then just note it and we can we can discuss about that so can we can we maybe centralize it somewhere because I feel like we can of.

**Harim Jung:** Chapter three, we're going to focus at one. But even though there is correct, the map is another reason that.

**Harim Jung:** Then another reason is not so huge.

**Harim Jung:** You know. So yeah, so that's your data. And if you find any other reason, then just note it and we can, we can discuss about that.

**Harim Jung:** So can we, can we maybe centralize this software? Because I feel like we cannot.

**상대방:** Expand the scope and then we know there is no expanded scope just with our scope is for cbs and CP only.

**Harim Jung:** Expand the scope and then we expand the scope just with our scope is for CBS and CP only.

**상대방:** It is already too narrow.

**Harim Jung:** It is already too narrow.

**상대방:** I understand that that.

**Harim Jung:** I understand that.

**상대방:** You expect that there might be many reasons to do this to create for sparsely even in this case but I think that there might not be huge.

**Harim Jung:** You expect that there might be many reasons to create for sparsely unit this case.

**Harim Jung:** But I think that there might not be huge.

**상대방:** Test to be manageable so even though there's some there but.

**Harim Jung:** Test we manageable. So even though there's some there, but.

**Harim Jung:** We, for example, our first half crisis 100% process. In that case, but there might be maybe around six or seven years or something like that. That means that the other is always there. So not just the data issue, thermopytes and other regions because of the data, the score might not be technically two of our steel.

**상대방:** Our first two accuracy is 100% for example in that case there might be an issue but there might be maybe around six or seventy or something like that the ten means that the other reasons always there so not just a data issue there might be some other reasons because of that the data the score might not be definitely two or five issues right.

**상대방:** Okay I think that if you find any other reason like publisher can cover the issue actually we cannot handle it this time.

**Harim Jung:** Okay, I think that if you find any other reason like coalition can cover the issue, actually we cannot handle it this time.

**상대방:** Because we do not have the policy information at all.

**Harim Jung:** Because we do not have pulse information at.

**Harim Jung:** All.

**상대방:** Right so we if we can use the whole information.

**Harim Jung:** Right. So if we can use the whole equation.

**상대방:** Then the policy information policy transaction then we can.

**Harim Jung:** Then the policy transaction.

**Harim Jung:** Then we can.

**상대방:** Declare that the code is in there or not.

**Harim Jung:** The credit the code is in there or not.

**상대방:** But if not maybe some policy is just with the tp coverage only.

**Harim Jung:** But if not.

**Harim Jung:** Maybe some policy needs just with tp coverage only.

**상대방:** But.

**Harim Jung:** But.

**Harim Jung:** We take coverage issue. Also we need to check because it doesn't matter. It's covered.

**상대방:** Coverage issue also we need to check because it doesn't matter it's coverage.

**상대방:** The issues that stolen car.

**Harim Jung:** The issue is that.

**Harim Jung:** Stolen car.

**상대방:** Already stored is not supposed to be insured but there is in short car that means that regardless of the coverage.

**Harim Jung:** Already is called kais nut is not supposed to be insured. But there is in short. Regardless of the coverage.

**상대방:** Whether there is clamped head or not it doesn't matter actually the car are not supposed to be insured is issued that is the matter.

**Harim Jung:** Whether it is take it or not, it doesn't matter actually the car that's supposed to be insured is ensured testimony.

**상대방:** Right.

**상대방:** So for the issue just discuss and then we can decide how to address some might not be handled because of the our resource information is not enough sometimes.

**Harim Jung:** So potential just discuss and then we can decide how to some might not be handled because of our resource information. Sometimes.

**상대방:** That fat does not.

**Harim Jung:** Fat does not.

**상대방:** Critical in deciding for your true positive.

**Harim Jung:** Critical in deciding for central biost.

**Harim Jung:** Imulus.

**상대방:** Okay.

**상대방:** Makes sense?

**상대방:** Can you please maybe add some explanation for the current patterns and how you add a flag in the documentation so that we can track it moving forward?

**Harim Jung:** Can you please maybe add some explanation for the current patterns and how you add flag in the documentation so that we can track it moving forward.

**상대방:** Do you mean this one?

**Harim Jung:** You mean this one?

**상대방:** Yeah.

**Harim Jung:** Yeah.

**상대방:** Yeah and also for the pattern is based on.

**Harim Jung:** And also for the pattern it's based on as.

**상대방:** Pattern yeah pattern I used AI so that might not be 100%

**Harim Jung:** Pect.

**Harim Jung:** Yeah. I use AI. So that might not be.

**Harim Jung:** 100%

**상대방:** Trust.

**Harim Jung:** Trust.

**Harim Jung:** Now.

**Harim Jung:** So this really looks okay, but we might need to change some semi magnetic propane.

**상대방:** Yeah mostly looks okay but we might need to change something we may need to group in I mean.

**상대방:** It is something like this but that's in some part we need to group it as well so I'm looking through all of those some might be quite close quite same so it might be different so we made a regroup here probably.

**Harim Jung:** It is something like this that in some part we need grouping as well. So I am looking through all of those. Some might be quite close. I say.

**Harim Jung:** Similarity from. So we might only regroup it.

**Harim Jung:** Probably.

**상대방:** Can you maybe regroup being if you have time this week?

**Harim Jung:** Can you maybe we will be if you have time this week.

**상대방:** So that we can know the.

**Harim Jung:** So that we can know.

**상대방:** More high level patterns instead of this I'm trying to see but it takes time so if possible I'm going to rearrange the grouping and then try to group it so maybe.

**Harim Jung:** The more high level patterns instead of this. I'm trying to see it. Can you take time so if possible I'm going to rearrange the grouping.

**Harim Jung:** And then try to repeat. So maybe.

**상대방:** Group one and tier one we might have separate one.

**Harim Jung:** One and to turn one we might have separate one.

**상대방:** So I also want to keep the current group as well and then we're going to have some self group for some of those and group yeah maybe we can use the existing one as a subcategory and then create a category or have a high like less granular category.

**Harim Jung:** So I also want to keep the current group as well.

**Harim Jung:** And then we will have some self growth for online corruption group. Yeah maybe we can use the existing one as a subcategory and then create a category.

**Harim Jung:** Less granular calories.

**상대방:** Yeah this is like a more granular category and then we can create like maybe another column and to show the.

**Harim Jung:** Like a more granular category and then we can create like maybe another column and to show.

**상대방:** Category like we can call it category and subcategory.

**Harim Jung:** The category that you can call it a category and subcategory.

**상대방:** That makes sense.

**Harim Jung:** Does that make sense?

**상대방:** It's a little bit.

**상대방:** Yeah.

**상대방:** Okay maybe I'm going to rearrange it and then reduce or land it and then talk more detail.

**Harim Jung:** Maybe I'm going to rearrange it and then.

**Harim Jung:** Talk about it.

**상대방:** Actually there are some more more pattern.

**Harim Jung:** Actually there are some more pattern.

**상대방:** There is more pattern and this one was I used chat TPT in copilot so it is not good it is not enough so actually I am trying to use the cloud code there's five or something.

**Harim Jung:** There is more pattern. And this one was I used.

**Harim Jung:** Chat copilot so it is not good. There is not enough.

**Harim Jung:** So actually I try to use.

**Harim Jung:** The cloud coder. There is an available problem or something.

**상대방:** So I have on my personal ID account for the code code and then I'm going to ask.

**Harim Jung:** So I have my personal idea account for the code. I'm going to ask.

**상대방:** Urea allow me to use those and then I'm going to apply the new code.

**Harim Jung:** It to your stores and I'm going to be apply.

**상대방:** Pattern to the data.

**Harim Jung:** Ing to the data.

**상대방:** Then then might be a little bit better because I check to every detail and some some need to be more chained I mean the most it works but some of those need to be because we have more detailed classification right the information was not fully well mapped.

**Harim Jung:** And the method will be better.

**Harim Jung:** Because I check to every detail and some need to be more changed. I mean the most, but some of those need to be because we have more detailed classification.

**Harim Jung:** But Jungkook mentioned was not fully.

**Harim Jung:** Well mapp.

**Harim Jung:** Ed.

**상대방:** But mostly okay mostly okay.

**Harim Jung:** But mostly okay.

**Harim Jung:** So I'm settling by.

**상대방:** So I'm checking one by one.

**Harim Jung:** One.

**상대방:** Okay I just want to explain what I'm doing and I think that the tooling also you to in your own way and I want to make a note on what we are trying to ask to the member companies so that at the time and the people you doing them I'm also I also have my list and combine and then we can ask the member company.

**Harim Jung:** Okay, I just want to explain what I'm doing and I think that the tool also you to in the old way and I want to make a note on what we are trying to ask to the labor companies so the data and the people you're doing. I'm also having my taste and combine and then you can ask the member company.

**상대방:** Maybe intuits.

**Harim Jung:** Maybe.

**상대방:** Okay sounds good so let's target to have the this patterns first and then we can discuss with members right so that we can do some interviews with members such as TDI to see how they visualize this and how we can reduce the positive false positive cases and also the reason why I like I'm concerned about the timeline and can provide some feedback like background there is because we had a meeting with a viva last Friday Julia was there and also their way off fraud crime was there like they and they share the performance for the EQ insights and then they express a lot of concerns on the sentence rate and the high false positive cases they are reviewing yeah definitely right and and then Julia just and the Julia and I share the initiative that we are working on because we are trying we are targeting to resolve those right to reduce the false positive and then we we told them that we will have some initial results by September. So that's the reason why.

**Harim Jung:** Sounds good. So let's start to have the this patterns first and then we can discuss with members right so that we can do some interviews with TDI to see how they visualize this and how we can reduce the positive false positive cases. And also the reason why I'm concerned about the timeline can provide some feedback like a background there is because we had a meeting with a last Friday.

**Harim Jung:** Charman was there and also their way P of fraud crime was there like they share the performance of where the EQ insights and then they expressed a lot of concerns on the sentence rate and the high false positive cases they are rebuilding.

**Harim Jung:** Yeah, definitely right and then Julia just shared the AI initiative that we are working on because we are trying we are targeting to resolve those right to reduce the transport here and then we told them that we will have some initial results by September. So that's the reason why.

**상대방:** I want us to be you know like he the timeline if if possible since we already share this either internal or externally and then I just want to make his progress so that's the reason why yeah that means that our project is very proper at this point exactly and also this is really valuable to the union size.

**Harim Jung:** I want us to find that if possible since we already share this either in internal or externally and then I just want to make it progress. So that's the reason why yeah that means that our project is very proper at this point. Exactly.

**Harim Jung:** And also this is really valuable to the insurance.

**상대방:** Right yeah okay that's good yeah so okay let's work I try to also find the reason and then my first one is the first is to crispify the pattern the identify the pattern yes and that pattern has shown the possibility of the postpartum APC especially if you see those one.

**Harim Jung:** Okay that's good. Yeah okay let's get more profit. I try to also find the reason that and my first one is the first is to crispify the pattern, the identified pattern. Yes. And the pattern has shown the possibility of the.

**상대방:** Yeah it is very high in the very high in the through positive.

**Harim Jung:** Spread high in the very high in the true positive.

**상대방:** And the third one is very high in false positive.

**Harim Jung:** And the third one is very high voltage fasting.

**상대방:** Yeah so we can see some of those a little bit clearer in the postpartum but maybe we might have better more solid evidence and the patterns for all of those and the gray area we might need to have some AI based and also identifying the pattern also we might need to create all of the program for those detecting the applying goals but AI might be much better to identify the pattern might be better rather than creating python script to detect this is which pattern something like that rather than that AI as we just put the history and then AI detected a pattern to make it much faster.

**Harim Jung:** Yeah, so we can see some of those need to create in the first class to pass that more soil to the headers and the patterns for all those. And the gray area might need to have some.

**Harim Jung:** AI based and also identifying the pattern also like into.

**Harim Jung:** All the problem for those detecting the upline doors. But AI might be much more spare to identify the pattern.

**Harim Jung:** Yeah. So then might be better. Rather than creating time to skip the to detect patterns, things like that rather than that AI as we just put history and then AI detected a pattern to make it much less.

**Harim Jung:** Time.

**상대방:** Yeah we just need to make sure it's accurate I know like test save us a lot of time but in the meantime they can also be inaccurate so we need also to manually check review make sure the labels are correct but I like the current you know like the labels but just make maybe we can make it more.

**Harim Jung:** Yeah, we just need to make sure it's accurate. I know like AI testing us a long time but in the meantime they can also be inaccurate. So we need also to manually check, reveal, make sure the label is not correct. But I like the current you like the labels but just make maybe we can make it more.

**상대방:** Yeah summarized this is actually threat from the AI so we're gonna look through it and then we have more better idea on the pattern if you look through all of those then and we just modified our pattern we just create pattern in our side and applied with AI to the individual cases.

**Harim Jung:** Right. Yeah. This is actually dripped from the AI. So we're going to look through it and then we might have more better idea on the pattern.

**Harim Jung:** Giving you all of those and we just modified our pattern. We just create pattern in our side and apply it with AI to the individual cases.

**상대방:** And then regarding the three 1979 no fraud alerts or this total 471 alerts is are they.

**Harim Jung:** And then regarding this 1979 no modelers or this total for 171 alerts.

**상대방:** No because you also select some data inconsistencies right it's they are not only the close investigations but also some from the discard orders okay never mind yeah just like want to make sure we what sample size you you make this right yeah I did it on the total one is 1100 already and actually the one the additional one is just for the latest speaker identifier all the vehicles so maybe 2001 to the model year I'm not sure that's involved in the dust prod.

**Harim Jung:** No, because you also select some data not only the source investigations but also some from the discard overs. Okay never mind. Yeah just like want to make sure what sample size you make.

**Harim Jung:** This off right the author one is 1100 already and actually the one the additional one is for the latest big oil makers.

**Harim Jung:** So maybe 2001 to the model year nationalism involved in those prod.

**상대방:** So we use related information but if we need it if we have time then we can add more beakers but within our timeline this is also a little bit tight already so we may focus on this information and then if we need more then we can add more.

**Harim Jung:** So we used the related information but we have time that we can add more beakers.

**Harim Jung:** But within our timeline this is also a little bit tight already.

**Harim Jung:** So in my focus on this situation and then if we need more mechanism.

**상대방:** Okay.

**상대방:** Yeah and Harim I think that you did a very good work on the shipping information so we started using anyway but one thing one critical issue we have is that we don't have more clear.

**Harim Jung:** And Har.

**Harim Jung:** Im, I think you did a very good work on the digital information. So we started to use it anyway.

**상대방:** So.

**상대방:** Okay.

**Harim Jung:** Okay so I have a question.

**Harim Jung:** So yeah I'm sorry. So regarding like indexing adding the in depth films for the data file like db.

**Harim Jung:** Arimon just a very long.

**상대방:** Hello.

**상대방:** Oh yeah.

**상대방:** Good could you.

**Harim Jung:** Yeah good.

**상대방:** Possibly 10 minutes and I'm still meeting with PhD okay.

**Harim Jung:** 10 minutes I'm still meeting like being okay.

**상대방:** 10 minutes okay thank you.

**Harim Jung:** Timing is okay take care.

**상대방:** Okay sorry yeah I was meeting I was called from f 12.

**Harim Jung:** Of.

**상대방:** Oh yeah so because my I changed my point and then authentication authentication is not working so I need to reset that one okay so I postpone the 10 10 minutes okay that's okay.

**Harim Jung:** So because I changed my poem.

**Harim Jung:** And.

**Harim Jung:** Birth certification authentic case is not working so I need to be set that one okay so I first pointed 10 minutes.

**Harim Jung:** Okay.

**상대방:** How was the question sorry.

**Harim Jung:** Now what's the question?

**Harim Jung:** Sorry.

**Harim Jung:** So you mentioned about like index maybe I lost it so do you want me to adding some more.

**Harim Jung:** Like column or adding some like code chains I just want to check.

**Harim Jung:** Out which one I thought were maybe I lost some point that's why I don't know I felt like you're asking me to like adding some index column or anything.

**상대방:** Which one are talking about.

**Harim Jung:** If not it's okay.

**상대방:** Oh no no I didn't ask you anything I just thank you for your works I mean we started to use the picker the past history it works good but the one thing is that it is not so detailed you know there is just months and especially when there's overlap in the data period past period it is not telling what was inside because the one policy can initial two times there shouldn't be no bullet so not easy to have more detailed information especially the code I mean if you have IBC data then we have full information for the coverage.

**Harim Jung:** Oh no no I didn't ask anything I just thank you for your workshop it works good but the one thing is that it is not so detailed you know there is just a month and especially when there's overlap in.

**Harim Jung:** The data period past period it is not 10% because the one part candidation two times there should be no bullet.

**Harim Jung:** So now needed to have multi-tended information especially code is IVC data then we have full information for the college.

**상대방:** But this one doesn't have it and the other one we have issues that quite over cases from Quebec but Quebec has no data in even in IBC so that what we cannot tell the one thing what we can do is that we get if we can get data from shipped I mean the member data premium information then probably they might be solved to a certain degree.

**Harim Jung:** But this one doesn't have it and the other one we have issues that.

**Harim Jung:** Pineapple case this problem but Tibet has no data even in IPC so that one cannot have the one thing what we can do is that we get if we can get data from shipped I mean the member data part premium information then probably they might be solved to a certain degree.

**상대방:** But we don't have it we are not very up there one.

**Harim Jung:** But we don't have it we understand okay thank you for very.

**상대방:** And also this remind me also maybe you mentioned that most of the cases are from Quebec right so maybe we can have a meeting with the super user from day jardine to see how like because like they mentioned that they are seeing less false positives but their osteoporosis.

**Harim Jung:** Many also maybe you mentioned that most of the cases are from quibbetic rights so maybe we can have.

**Harim Jung:** A meeting with the super user from day 13 to see how like they didn't mention that they are seeing less false positives but there are still false objectives.

**상대방:** So maybe after once we confirm the.

**Harim Jung:** So maybe after once we confirm.

**Harim Jung:** The pattern and then we can talk to the day driving the super user and remember what she yeah yeah observes and based on the alerts that they were receiving.

**상대방:** Pattern and then we can talk to day Jung the super user and remember her name is Jackie and then ask what she yeah yeah observes and based on the alerts that they receive.

**상대방:** Yeah right yeah.

**상대방:** Okay.

**상대방:** Okay thank you and just keep on so if you need any help so then we can talk anytime anything you want to discuss then just call a meeting anytime then we can resolve it so and the other one what I'm doing is that I'm trying to use the program the illustrator right show to you I created with the credit card so that one is based upon separate database for each one claim premium CP and all those data structures with complicated but I think that if you can use the chronic history for the beaker then that might be easier to express it but I need to in order to day one I need full step program in my PC but I'm that's why I'm reading the new PC one second UPC then I'm gonna then all of those including the container I mean.

**Harim Jung:** And just keep on so if you need any help then we can talk anytime and anything you want to discuss then just call the building every time you can reserve it.

**Harim Jung:** The other one what I'm doing is that I'm trying to use the program to illustrate it right to you I created this protocol so that one is based upon separate database for each one claim premium CPU and all those data structure is a little bit complicated but I think that if you can use.

**Harim Jung:** The chronicle history for the picker to express it but I need to.

**Harim Jung:** In order to be on I need to pull through step program in my PC and that's what I'm wearing the new piece in one side you can see that I'm going to know all of those including the.

**Harim Jung:** Container I mean.

**상대방:** So yeah I have a quick question regarding the new PC so did you have any update for.

**Harim Jung:** So yeah regarding the new PC so did you have any updates for.

**상대방:** That?

**Harim Jung:** That? Because yeah last week you have mentioned that we can upgrade right then.

**상대방:** Yeah last week Julia mentioned that we can upgrade right at the.

**상대방:** I'm still waiting because of that I'm still waiting for moving the program from my PC to here.

**Harim Jung:** I'm still waiting because of that I'm still waiting for moving the program put on my PC to here.

**상대방:** Same here yeah because yeah because I just had really last year but I think because of the CPU requirement for the adjust.

**Harim Jung:** Same here yeah because yeah I just have really.

**Harim Jung:** Last year but I think because of the CPU requirement for the AI adjust.

**상대방:** Me to have the new laptop the upgraded one so that we can run some faster like faster in the.

**Harim Jung:** You to have a new laptop that created one so that we can run cell AI that you go faster and that's faster in.

**Harim Jung:** The way that.

**상대방:** Upgrade laptop.

**Harim Jung:** One yeah I'm not sure how many we can run it in my PC.

**상대방:** Yeah I'm not sure how many we can run it in my PC actually yeah are you really trained AI model using the MacBook because I know MacBooks trip is faster yeah that's what I did before but things our company all use no walls I don't know how fast it will be.

**Harim Jung:** Model using the light boob because I know MacBooks trivia faster as more that I did before but things our company I use the nobles I don't know how fast it will be.

**Harim Jung:** Used to be much better than yeah anyway yeah.

**상대방:** Much better than current PC anyway yeah anyway yeah it is.

**상대방:** Okay thank you and maybe we can have a little bit of for Julia okay okay yeah thank you.

**Harim Jung:** Okay thank you and then maybe we can have a little bit of call thank you.
