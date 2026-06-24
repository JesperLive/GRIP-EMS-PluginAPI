-- My First EMS Plugin
-- An example plugin for the GRIP-EMS Plugin API. MIT-licensed; copy it freely.
--
-- It shows the shape of a real plugin end to end:
--   * a hard dependency on GRIP-EMS (see the .toc)
--   * the version handshake
--   * a capability check before using a tier
--   * event subscriptions (and how to drop them)
--   * a Tier 2 data read behind a slash command
--   * a variable provider (a ~name~ value source)
--   * a condition (a named boolean usable in a variable body)

local ADDON_NAME = ...

-- We keep the handles we get back from On() so we could cancel them later.
local subscriptions = {}

-- Return true if the running API advertises a capability id.
local function HasCapability(API, cap)
    for _, c in ipairs(API:GetCapabilities()) do
        if c == cap then
            return true
        end
    end
    return false
end

local function Init()
    local API = GRIPEMS and GRIPEMS.API
    if not API then
        return -- GRIP-EMS is not loaded; nothing to extend.
    end

    -- Bail out cleanly on an EMS too old for the API version we use.
    local ok, reason = API:RequireVersion(1)
    if not ok then
        print("My First EMS Plugin needs a newer GRIP-EMS: " .. tostring(reason))
        return
    end

    -- Tier 1: react when a sequence is created. The payload is (name, data);
    -- the first argument is the name string, not a table.
    subscriptions[#subscriptions + 1] = API:On("SEQUENCE_CREATED", function(name)
        print("MyFirstPlugin saw a new sequence: " .. tostring(name))
    end)

    -- Tier 4: a variable provider. When a user puts ~myfirst_groupsize~ in a
    -- sequence, EMS asks us to resolve it (only after the user's own variables
    -- and gear variables miss). Return a plain non-secret scalar, or nil for
    -- names that are not ours.
    if HasCapability(API, "variables") then
        API:RegisterVariableProvider("myfirst_groupsize", {
            id = "myfirst_groupsize",
            name = "My First Plugin: group size",
            Resolve = function(_, varName)
                if varName == "myfirst_groupsize" then
                    return GetNumGroupMembers() -- a number; never secret-tagged
                end
                return nil
            end,
        })
    end

    -- Tier 4: a condition. A user can branch on it inside a variable body, e.g.
    --   GRIPEMS.API:EvaluateCondition("myfirst_in_group") and "Spell A" or "Spell B"
    if HasCapability(API, "conditions") then
        API:RegisterCondition("myfirst_in_group", {
            id = "myfirst_in_group",
            name = "My First Plugin: in a group",
            Evaluate = function()
                return IsInGroup()
            end,
        })
    end

    -- Tier 2: read state on demand. /myfirst prints the active sequences and context.
    SLASH_MYFIRSTPLUGIN1 = "/myfirst"
    SlashCmdList["MYFIRSTPLUGIN"] = function()
        local list = API:GetSequenceList()
        print(("MyFirstPlugin: %d active sequence(s), context = %s")
            :format(#list, tostring(API:GetCurrentContext())))
        for _, s in ipairs(list) do
            print((" - %s (%d/%d, %s)"):format(s.name, s.currentStep, s.stepCount, s.stepFunction))
        end
    end
end

-- Register on PLAYER_LOGIN, not at file scope: it is the conventional point
-- where EMS is fully built and GRIPEMS.API is ready.
local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function()
    Init()
end)
