CodeMirror.defineSimpleMode("algo", {
    // The start state contains the rules that are initially used
    start: [
      // The regex matches the token, the token property contains the type
        {regex: /  /, token: "string"},
        // You can match multiple tokens at once. Note that the captured
        // groups must span the whole string in this case
        {regex: /(function|procedure|program)(\s+)(\w*)/,
        token: ["keyword", null, "variable-2"]},
        // Rules are matched in the order in which they appear, so there is
        // no ambiguity between this one and the one above
        {regex: /(?:end)?(?:program|function|procedure|if|for|while)\b/,
        token: "keyword"},
        {regex: /(?:kamus|algoritma|return|else|repeat|until|do|const|type|of|array)\b/, 
        token: "keyword"},
        {regex: /\b(?:true|false|in(?:\/out)?|integer|string|real|char(?:acter)?)\b/, 
        token: "atom"},
        // {regex: /0x[a-f\d]+|[-+]?(?:\.\d+|\d+\.?\d*)(?:e[-+]?\d+)?/i,
        {regex: /\d+/,
        token: "number"},
        // {regex: /\/\/.*/, token: "comment"},
        // {regex: /\/(?:[^\\]|\\.)*?\//, token: "variable-3"},
        // A next property will cause the mode to move to a different state
        {regex: /\{/, token: "comment", next: "comment"},
        {regex: /(?<!in)[-+\/*=<>!]+(?!out)/, token: "operator"},
        // indent and dedent properties guide autoindentation
        {regex: /kamus$/, token: "keyword", indent: true, next: "kamus", sol: true},
        {regex: /(?:print|write|output|input|read)\b/, token: "variable-3"},
        // {regex: /\w*/, token: "variable"}, 
        // You can embed other modes with the mode property. This rule
        // causes all code between << and >> to be highlighted with the XML
        // mode.
        // {regex: /<</, token: "meta", mode: {spec: "xml", end: />>/}},
        // {regex: /(array)\s\[(\d)\.{2}(\w+)\]\s(of)\s(\w+)/,
        // token: ["keyword", "number", "variable-2", "keyword", "atom"]}
    ],
    // The multi-line comment state.
    comment: [
      {regex: /.*?\}/, token: "comment", next: "start"},
      {regex: /.*/, token: "comment"}
    ],
    // The meta property contains global information about the mode. It
    // can contain properties like lineComment, which are supported by
    // all modes, and also directives like dontIndentStates, which are
    // specific to simple modes.
    // meta: {
    //   dontIndentStates: ["comment"],
    //   lineComment: "//"
    // },
    // type definition
    kamus: [
        {regex: /(type) (\w) </, token: ["variable", "operator"]},
        {regex: /(array)\s?\[(\d)..(\w+)\]\s(of)\s(\w+)/,
        token: ["keyword", "number", "variable-3", "keyword", "atom"]},
        {regex: /algoritma$/, token: "keyword", dedent: true, next: "start", sol: true},
    ]
  });