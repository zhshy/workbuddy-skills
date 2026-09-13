# First-use intake

Use the bundled questionnaire as the default intake for a new or preference-light request. Open or attach `assets/intake-questionnaire/index.html`, ask whether the user wants to complete it or use mainstream defaults, and continue from the prompt it generates when completed. Do not replace this page with the host application's native multiple-choice UI.

The questionnaire output or current written brief is the single intake authority. Do not add a decision list, host-native choice widget or improvised questions. Once the brief includes preferences/constraints, start immediately and resolve any remaining optional fields with the skill defaults. Do not cite an earlier destination, previous run, saved memory or old project unless the user explicitly requests reuse. Do not proactively explain legacy issues, exclusions or internal workflow.

If the user supplied a complete brief (destination, dates or duration, travelers, rhythm/default permission, interests and constraints), skip the questionnaire and start immediately. If the brief supplies only destination, dates/duration and travelers, show the questionnaire and ask exactly once: `其他内容要填一下问卷，还是全部按主流默认方案安排？如果不需要问卷，直接回复“按默认”即可。` A refusal or default permission completes intake and must start work without another question. A destination-only request is also valid without a questionnaire when the user explicitly asks the Agent to choose sensible defaults. If the host cannot open local HTML, provide the same one-question choice and use a short conversational fallback only when the user elects to provide preferences.

The only user-facing transport/accommodation note should be: booked transport or accommodation can be supplied as screenshots or text; otherwise those sections remain pending. Do not explain edition boundaries, excluded modules, internal architecture or comparison features unless the user asks.

The public questionnaire contains only core handbook inputs: destination; dates or days; travelers and relationship; broad budget; pace; interests; must-go places; exclusions; food/accessibility/special requirements. It never asks for flight or hotel selection criteria and never triggers commercial recommendations.

Every optional field has a neutral default. Missing fields do not block generation. Use mainstream first-visit defaults, label material assumptions and keep unprovided transport or accommodation pending.

Suggested first response:

> 我可以为你制作一份完整的个性化旅行手册，包括每日行程、景点、购物、当地体验、餐饮、准备清单、语言锦囊和旅行贴士，并生成适合手机与电脑查看的网页。
>
> 这是 1–3 分钟的旅行需求问卷，填完后把它生成的提示词发给我即可。如果不想填，直接回复“按默认”，其他内容会按保守、主流的方案安排，不再追问。

Link `assets/intake-questionnaire/index.html` when local file links are supported. Do not paste its HTML into conversation.
