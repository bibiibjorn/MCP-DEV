# Task Completion Protocol

## For AI Assistant: Plan Usage Awareness

### When User Says: "I'm at X% plan usage"

**IMMEDIATELY:**

1. **Assess Urgency**
   - < 50%: Normal pace, comprehensive responses
   - 50-70%: Focus mode - prioritize completion
   - 70-85%: FAST mode - essential work only
   - 85-95%: CRITICAL - wrap up current task NOW
   - > 95%: STOP - only emergency fixes

2. **Current Task Priority**
   - ✅ Complete in-progress task FIRST
   - ❌ Don't start new large tasks
   - 💾 Save all progress immediately
   - 📝 Document what's done/pending

3. **Response Strategy by Usage Level**

### 50-70% Usage: Focus Mode
- Complete current task fully
- Skip extensive testing
- Minimal documentation
- No exploratory work

### 70-85% Usage: Fast Mode
- **ONE action per response**
- Verify syntax only
- Critical fixes only
- Create TODO for remaining work

### 85-95% Usage: Critical Mode
- **FINISH CURRENT EDIT ONLY**
- No new features
- No refactoring
- Quick syntax check
- Exit gracefully

### 95%+ Usage: Emergency Mode
- **STOP WORK**
- Save current state
- List what's pending
- Exit immediately

---

## Task Completion Checklist

### Before Starting Any Task (Check User's Plan Usage!)

```markdown
- [ ] Current plan usage < 70%?
- [ ] Task can complete in 5-10 responses?
- [ ] Have rollback plan if interrupted?
- [ ] Critical files backed up?
```

### During Task (Monitor Progress)

```markdown
- [ ] Break large tasks into small commits
- [ ] Test syntax after each edit
- [ ] Document progress in TODO
- [ ] Can pause and resume?
```

### Completion Criteria

```markdown
- [ ] All syntax valid
- [ ] Core functionality works
- [ ] Documented what was done
- [ ] No broken state
```

---

## Quick Decision Tree

```
User reports plan usage
         |
         v
    < 70%?  → Continue normally
         |
         v
    70-85%? → Finish current task, then STOP
         |
         v
    85-95%? → Complete current file edit, then STOP
         |
         v
    > 95%?  → STOP IMMEDIATELY, save state
```

---

## Communication Protocol

### At 70%+ Usage, ALWAYS Include:

```markdown
⚠️ PLAN USAGE: X% - Working in FAST MODE

Current Task: [task name]
Status: [% complete]
ETA: [N responses to complete]

Options:
1. ✅ Finish current task (N responses)
2. ⏸️ Pause and save state
3. ❌ Stop now
```

---

## Emergency Save Protocol

If user says "STOP" or usage > 95%:

1. Save current file (if editing)
2. Update TODO with status
3. Create RESUME.md with:
   - What was being done
   - What's complete
   - What's next
   - How to continue

---

## Example Usage

**User:** "I'm at 88% plan usage"

**Assistant Response:**
```markdown
⚠️ PLAN USAGE: 88% - CRITICAL MODE

Current Task: Fixing TMSL export for large models
Status: 90% complete
ETA: 2 responses to complete

Action: Finishing current file edits only, then stopping.

What I'll do:
1. Save model_exporter.py changes ✓
2. Quick syntax check ✓
3. Update documentation ✓
4. STOP and create status summary

Proceeding with completion...
```

---

## For Users: How to Help

**At start of session:**
- Check your plan usage percentage
- Tell me if you're > 50%

**During work:**
- Update me if you cross 70%, 85%, 95%
- Say "STOP" if you need to pause

**Best practice:**
- Start complex tasks when usage < 50%
- Save risky work for after reset
- Break large projects into sessions
