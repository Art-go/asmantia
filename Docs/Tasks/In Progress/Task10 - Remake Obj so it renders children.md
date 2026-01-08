---
tags:
  - task
Status: In Progress
id: 10
aliases:
  - task#10
---
>[!tldr] Quick Description
>If a = Obj() has b,c,d as children^[Which it should keep track of after [[Task9 - Make Objects keep track of their children]]]
>When on render it should call .render() of b,c,d


## Steps
- [ ] add it to Obj()
- [ ] add super() to Renderers [^1]
- [ ] ? maybe some caching? idk, it just kinda makes sense ^37aad1

[^1]: As stated [[Task10 - Remake Obj so it renders children#^37aad1|further down]], maybe instead make into req_render which does DFS of a tree, and stores the result in a list on each step.  
	
	There is also a problem of cache invalidation, but i guess we can just keep track on validity and if it is valid, we can just reuse it.
	so if A->B,C; B becomes invalid => A becomes invalid; A checks validity of itself when asked to render => A sees what B is invalid => A requests B to recalculate cache => A adds valid cache; A checks C => it's valid so it just reuses it.
	
	so it should be O(depth)
