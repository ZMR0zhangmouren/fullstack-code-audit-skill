# Node.js Sink Reference (for node-route-tracer and vulnerability specialty alignment)

This file is the Sink determination baseline for the Node.js full-stack extension. Sink classification codes are consistent with the SEVERITY type codes:
`SQL / NOSQL / CMD / SSRF / XSS / DOMXSS / SSTI/TPL / FILE / WRITE / UPLOAD / ARCHIVE / REDIR / DESER / EXPR / PROTO / REDOS / SESS / CRYPTO / CSRF / CFG`.

Each type section provides:
- **Sink API list (with package names)**: high-risk call points that actually exist in Node.js native or the npm ecosystem;
- **Controllable parameter positions**: which argument, which field of the options object, or which chained-call input is most often polluted by external input;
- **Reference Barriers**: validation, isolation, or configuration means to focus on when mitigating / detecting.

> Note: the same API can be a Sink or a legitimate call; whether it constitutes a vulnerability depends on "whether externally controllable input enters a dangerous parameter position without validation".

---

## SQL

### Native Drivers

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `connection.query(sql, callback)` | `mysql` / `mysql2` | 1st argument `sql` | Placeholder `?` + parameter array; string concatenation forbidden |
| `connection.query(options, callback)` | `mysql` / `mysql2` | `options.sql` | Same as above |
| `connection.execute(sql, values, callback)` | `mysql2` | 1st argument `sql` | Prepared statement + parameterized values |
| `client.query(text, values, callback)` | `pg` | 1st argument `text` | `$1, $2` placeholders + values array |
| `pool.query(text, values)` | `pg` | 1st argument `text` | Same as above |

### ORM / Query Builder

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `knex.raw(sql, bindings)` | `knex` | 1st argument `sql` | Placeholder `?` / `:key:` + bindings |
| `sequelize.query(sql, options)` | `sequelize` | `sql` concatenated directly outside `options.replacements` / `options.bind` | `replacements` / `bind` parameterization; `type: QueryTypes.SELECT` read-only |
| `Model.findAll({ where: sequelize.literal(userInput) })` | `sequelize` | `sequelize.literal` argument | Avoid user input entering `literal`; field whitelist |
| `repository.query(rawSql)` | `typeorm` | 1st argument | Parameterized queries; `Repository.query(sql, params)` |
| `getManager().query(rawSql)` | `typeorm` | 1st argument | Same as above |

### Dynamic Fragments (Cannot Be Parameterized; Whitelist Required)

- `ORDER BY ${userColumn}` — column name/alias slot
- `LIMIT / OFFSET ${userNumber}` — numeric slot (requires strong integer conversion and range validation)
- `FROM ${userTable}` — table name slot
- `WHERE ${dynamicFragment}` — condition fragment slot

---

## NOSQL

### MongoDB / Mongoose

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `collection.find(query)` | `mongodb` | `query` object as a whole | Validate object key whitelist; disable `$where` |
| `collection.findOne(query)` | `mongodb` | `query` object | Same as above |
| `Model.find(query)` | `mongoose` | `query` object | Same as above; use mongoose schema static types |
| `Model.findOne(query)` | `mongoose` | `query` object | Same as above |
| `Model.find({ $where: userInput })` | `mongoose` | `$where` field | Forbid `$where`; `mongoose.set('sanitizeFilter', true)` |
| `Model.find({ field: { $regex: userInput } })` | `mongoose` | `$regex` field | Regex whitelist / `RegExp.escape` |
| `Model.where().$where(userInput)` | `mongoose` | `$where` argument | Forbidden |

### Redis

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `redisClient.eval(script, ...)` | `redis` / `ioredis` | 1st argument Lua `script` | Avoid script concatenation; use EVALSHA + pre-registered scripts |
| `redisClient.sendCommand(command)` | `redis` / `ioredis` | `command` array elements | Command whitelist; key name escaping |

### Elasticsearch

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `client.search({ body: userObject })` | `@elastic/elasticsearch` | `body.query` object | Query DSL whitelist; avoid direct JSON concatenation |

---

## CMD

### child_process

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `exec(command, callback)` | `child_process` | 1st argument `command` | Array-style arguments: `execFile` / `spawn`; avoid shell interpretation |
| `execSync(command)` | `child_process` | 1st argument `command` | Same as above |
| `execFile(file, args, options)` | `child_process` | `args` array elements | Do not set `options.shell = true`; array-style arguments |
| `spawn(command, args, options)` | `child_process` | 1st argument when `options.shell = true` | Default `shell: false`; array-style arguments |
| `fork(modulePath, args)` | `child_process` | `args` array elements | Validate argument content |

### Indirect Command Execution

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `shelljs.exec(cmd)` | `shelljs` | 1st argument `cmd` | Forbid user input entering the command string |
| `node-cmd.run(cmd)` | `node-cmd` | 1st argument `cmd` | Same as above |

---

## SSRF

### HTTP Clients

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `axios.get(url, config)` | `axios` | 1st argument `url`; `config.baseURL` + `config.url` concatenation | URL whitelist / host whitelist; disable `maxRedirects` or restrict protocols |
| `axios.request(config)` | `axios` | `config.url` / `config.baseURL` | Same as above |
| `fetch(url, init)` | native `fetch` / `node-fetch` | 1st argument `url` | Protocol whitelist (http/https); host whitelist |
| `got(url, options)` | `got` | 1st argument `url` | Same as above |
| `request(url, options)` | `request` / `postman-request` | 1st argument `url` | Same as above |
| `http.get(url, callback)` | native `http` / `https` | 1st argument `url` | Same as above |
| `undici.request(url, options)` | `undici` | 1st argument `url` | Same as above |
| `urllib.request(url, options)` | `urllib` | 1st argument `url` | Same as above |

### Special Scenarios

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| Webhook callback URL | business code | user-provided URL string | URL protocol/host whitelist; disable file:// / gopher:// / dict:// |
| PDF generation URL (puppeteer / html-pdf) | `puppeteer` / `html-pdf` | rendering target URL | forbid intranet / metadata addresses; URL whitelist |
| Image download URL | `sharp` / `jimp` / `axios` | URL string | whitelist + response Content-Type validation |

---

## XSS

### Server-Side Output

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `res.send(markup)` | Express native | 1st argument (when Content-Type is text/html) | HTML-encode output; use template engine auto-escaping |
| `res.render(view, locals)` | Express native | unencoded fields in `locals` | template engine default escaping; disable raw output such as `{{{ }}}` / `<%-` |
| `ejs.render(template, data)` | `ejs` | `template` or `data` fields | `<%= %>` auto-encoding; avoid `<%- userInput %>` |
| `pug.render(template, data)` | `pug` | `data` entering `!=` positions | avoid `!=` outputting user data |
| `nunjucks.renderString(template, context)` | `nunjucks` | `template` / `context` | default escaping; disabling `autoescape` is dangerous |
| `handlebars.compile(template)(context)` | `handlebars` | `template` / `context` | default HTML encoding; using `{{{ }}}` requires explicit approval |
| `mustache.render(template, view)` | `mustache` | `template` / `view` | default escaping; watch out for tripleMustache |

### Encoding/Escaping Configuration

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `xss(userInput, options)` | `xss` | 1st argument; `options.whiteList` | configure a strict whitelist; forbid `style` / `on*` events |
| `DOMPurify.sanitize(dirty)` | `dompurify` | 1st argument | configure `FORBID_ATTR` / `FORBID_TAGS` on both server and client |

---

## DOMXSS

### Client-Side DOM Manipulation

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `document.write(userInput)` | browser native | 1st argument | avoid writing location.hash / search directly |
| `element.innerHTML = userInput` | browser native | right-hand assignment | use `textContent` / `innerText` instead; DOMPurify first |
| `element.outerHTML = userInput` | browser native | right-hand assignment | same as above |
| `document.createRange().createContextualFragment(html)` | browser native | `html` argument | sanitize first |
| `jQuery.html(userInput)` | `jquery` | 1st argument | use `.text()` instead; configure `DOMPurify` |
| `jQuery.append(userInput)` | `jquery` | 1st argument | same as above |
| `React dangerouslySetInnerHTML={{ __html: userInput }}` | React native | `__html` field | must sanitize first; never place unprocessed external HTML directly |
| `Vue v-html="userInput"` | Vue native | `v-html` expression | same as above |

### JavaScript Execution Sinks

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `eval(userInput)` | browser/Node native | 1st argument | forbid any external input from entering |
| `new Function(userInput)` | browser/Node native | 1st argument | forbidden |
| `setTimeout(userCode, delay)` | browser/Node native | 1st argument when it is a string | pass functions only |
| `setInterval(userCode, delay)` | browser/Node native | 1st argument when it is a string | pass functions only |
| `window.location = userUrl` | browser native | right-hand assignment | URL whitelist; avoid the `javascript:` pseudo-protocol |

---

## SSTI/TPL

### Server-Side Template Engines

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `ejs.render(userTemplate, data)` | `ejs` | `userTemplate` | forbid user-controlled template strings; template file whitelist |
| `pug.compile(userTemplate)` | `pug` | `userTemplate` | same as above |
| `nunjucks.renderString(userTemplate, context)` | `nunjucks` | `userTemplate` | same as above |
| `handlebars.compile(userTemplate)` | `handlebars` | `userTemplate` | same as above; restrict helper registration |
| `mustache.render(userTemplate, view)` | `mustache` | `userTemplate` | same as above |
| `res.render(view, locals)` | Express native | `view` name | view name whitelist; forbid user-controlled template paths |

### Template Expression Evaluation

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `lodash.template(userTemplate)(data)` | `lodash` | `userTemplate` | forbid user input controlling the template |
| `dot.template(userTemplate)` | `dot` (npm package; repo olado/doT) | `userTemplate` | same as above |
| `eta.render(userTemplate, data)` | `eta` | `userTemplate` | same as above |

---

## FILE/WRITE

### File Read

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `fs.readFile(path, callback)` | native `fs` | 1st argument `path` | path normalization + prefix whitelist; forbid `..` / null bytes |
| `fs.readFileSync(path)` | native `fs` | 1st argument `path` | same as above |
| `fs.createReadStream(path)` | native `fs` | 1st argument `path` | same as above |
| `fs.open(path, flags, callback)` | native `fs` | 1st argument `path` | same as above |
| `res.sendFile(path, options)` | Express native | 1st argument `path` | `root` option to confine the root directory; path normalization |
| `path.join(base, userPath)` | native `path` | 2nd argument onward | validate base first; check prefix after normalization |
| `path.resolve(userPath)` | native `path` | 1st argument onward | compare against the root directory; avoid relative-path escape |

### Path Traversal Patterns

- `../` / `..\` directory traversal
- URL-encoded `%2e%2e%2f`
- Null byte `%00` (legacy Node / underlying C libraries)
- Symlinks/hardlinks pointing to sensitive files

### File Write

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `fs.writeFile(path, data, callback)` | native `fs` | 1st argument `path`; 2nd argument `data` | path prefix whitelist; forbid user-controlled extensions landing in web directories |
| `fs.writeFileSync(path, data)` | native `fs` | 1st / 2nd argument | same as above |
| `fs.appendFile(path, data, callback)` | native `fs` | 1st / 2nd argument | same as above; prevent log injection |
| `fs.createWriteStream(path)` | native `fs` | 1st argument `path` | same as above |
| `fs.open(path, 'w', callback)` | native `fs` | 1st argument `path` | same as above |

### Dangerous Patterns

- User-controlled file name + write into `public/` / `static/` directories → WebShell
- User-controlled path + write into configuration directories → configuration override
- User-controlled log path → log injection + path traversal

---

## UPLOAD

### Upload Receiving

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `multer({ dest: folder })` | `multer` | `dest` / `filename` callback; `fileFilter` | `fileFilter` extension whitelist + MIME; rename to random names |
| `multer({ storage: diskStorage({ destination, filename }) })` | `multer` | `destination` / `filename` callbacks | restrict landing directory; forbid original file names landing directly |
| `busboy.on('file', (name, file, info) => {})` | `busboy` | `info.filename` | file name whitelist; restrict landing location |
| `formidable({ uploadDir })` | `formidable` | `uploadDir`; `file.originalFilename` | restrict directory; rename |
| `req.files` / `req.file` | Express + `multer` | `file.originalname` / `file.mimetype` | backend validation; do not rely on client MIME |

### Key Checkpoints

- Extension: whitelist > blacklist; watch for double extensions `.jpg.php`
- Content-Type: client-forgeable; backend magic-byte / extension cross-validation is mandatory
- File size: `limits.fileSize`
- Landing path: forbid executable files in web-accessible directories
- Renaming strategy: UUID / hash; keep the original name for display only and sanitize it

---

## ARCHIVE

### Extraction APIs

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `extractZip(zipPath, { dir })` | `extract-zip` | `zipPath`; `dir` | validate `entry.fileName` per entry; reject `..` |
| `AdmZip.extractAllTo(targetPath, overwrite)` | `adm-zip` | `targetPath` | validate entry names; restrict landing directory |
| `tar.extract({ file, cwd })` | `tar` | `file`; `cwd` | `strip` parameter; validate entry paths |
| `yauzl.open(zipPath, options, callback)` | `yauzl` | `zipPath`; `entry.fileName` | validate `fileName`; symlink review |
| `unzipper.Open.file(zipPath)` | `unzipper` | `zipPath`; `entry.path` | same as above |

### Zip Slip Patterns

- `entry.fileName` / `entry.path` containing `../` → written outside the target directory
- Symlink entries → pointing to sensitive files such as `/etc/passwd`
- Absolute-path entries → overwriting system files

---

## REDIR

### Express / Connect

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `res.redirect(url)` | Express native | 1st argument `url` | URL allowlist; allow relative paths only with path-prefix validation |
| `res.redirect(status, url)` | Express native | 2nd argument `url` | same as above |
| `res.location(url)` | Express native | 1st argument `url` | same as above |

### Authentication / SSO Flows

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `passport.authenticate(..., { successRedirect: userUrl })` | `passport` | `successRedirect` / `failureRedirect` | hardcoded or whitelist |
| OAuth `redirect_uri` | `passport-oauth2` / business code | callback URL | strictly match the pre-registered redirect_uri |
| OIDC `post_logout_redirect_uri` | `openid-client` | post-logout redirect URL | whitelist |

### Common Parameter Names

- `returnUrl` / `return_url` / `redirect` / `redirectUrl` / `next` / `goto` / `continue` / `callback`

---

## DESER

### JSON / JS Native

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `JSON.parse(userInput)` | native | 1st argument | schema validation first; prevent `__proto__` pollution and ReDoS large keys |
| `eval(userInput)` | native | 1st argument | completely forbidden |
| `new Function(userInput)` | native | 1st argument | completely forbidden |

### Third-Party Serialization

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `serialize.unserialize(userInput)` | `node-serialize` | 1st argument | forbid processing untrusted input |
| `serialize(obj)` output passed into `eval(serialized)` or `new Function('return ' + serialized)()` | `serialize-javascript` | code string restored for execution | trust the source only; avoid function/regex restoration |
| `yaml.load(userInput)` | `js-yaml` | 1st argument | use `yaml.safeLoad` / `yaml.load` with `!!js/function` disabled |
| `msgpack.decode(userInput)` | `msgpack-lite` / `msgpack` | 1st argument | type whitelist; avoid typeless mode |
| `bson.deserialize(userInput)` | `bson` | 1st argument | limit buffer size; validate object structure |

### Prototype Pollution Entry Points

- `JSON.parse` + subsequent `Object.assign({}, parsed)` without sanitizing `__proto__`
- `merge({}, userInput)` (see the PROTO section)

---

## EXPR

### Dynamic Execution

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `eval(expression)` | native | 1st argument | forbidden |
| `new Function(expression)` | native | 1st argument | forbidden |
| `vm.runInThisContext(code)` | native `vm` | 1st argument `code` | forbid user input |
| `vm.runInNewContext(code, sandbox)` | native `vm` | 1st argument `code` | sandbox isolation cannot replace input validation |
| `vm.runInContext(code, context)` | native `vm` | 1st argument `code` | same as above |
| `vm.Script(code).runInContext(ctx)` | native `vm` | constructor argument `code` | same as above |

### Expression Evaluation Libraries

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `Parser.parse(expr).evaluate(context)` | `expr-eval` / `mathjs` | expression string | expression whitelist; disable dangerous functions |
| `math.evaluate(expression)` | `mathjs` | expression string | restrict the function set; use `math.parse` + whitelist |
| `safeEval(expression)` | `safe-eval` / `notevil` | expression string | still must validate source and expression scope |

---

## PROTO

### High-Risk Prototype Pollution APIs

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `_.set(object, path, value)` | `lodash` | `path` containing `__proto__.x` / `constructor.prototype.x` | upgrade to a non-vulnerable version; path whitelist |
| `_.merge(target, source)` | `lodash` | `source` object keys `__proto__` / `constructor` | upgrade to ≥4.17.21; use `lodash/fp` immutable merge |
| `_.defaultsDeep(object, sources)` | `lodash` | polluted objects in `sources` | same as above |
| `_.assignIn(target, source)` | `lodash` | `source` object keys | avoid untrusted sources entering |
| `Object.assign(target, source)` | native | `source` containing `__proto__` / `constructor` | sanitize keys first; use `Object.create(null)` |
| `Object.defineProperty(target, key, descriptor)` | native | `key` being `__proto__` | validate keys; avoid prototype pollution |
| `merge(target, source)` | `deep-extend` / `extend` / `utils-merge` | `source` object | upgrade to safe versions; key whitelist |
| `hoek.merge(target, source)` | `hoek` | `source` object | upgrade to safe versions |
| `JSON.parse(userInput)` + post-deserialization traversal assignment | business code | user-input JSON keys | sanitize `__proto__` / `constructor` / `prototype` |

### Pollution Detection Barriers

- Input key blacklist: `__proto__`, `constructor`, `prototype`
- Use `Object.create(null)` or `Map` instead of plain objects to store untrusted keys
- Use `Object.freeze(Object.prototype)` as defense in depth

---

## REDOS

### Regex Construction

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `new RegExp(userPattern, flags)` | native | 1st argument `pattern` | forbid user input constructing regex; when unavoidable use ReDoS detection |
| `new RegExp(userPattern)` | native | 1st argument `pattern` | same as above |
| `string.match(userRegex)` | native | regex object or string | avoid user input used directly as regex |
| `string.search(userRegex)` | native | same as above | same as above |
| `string.replace(userRegex, replacement)` | native | same as above | same as above |
| `string.split(userRegex)` | native | same as above | same as above |
| `validator.matches(input, pattern)` | `validator` | `pattern` argument | use built-in whitelist patterns only |
| `validator.isEmail(input, options)` | `validator` | custom `host_blacklist` in `options` | avoid user-controllable regex |

### ReDoS Detection Tools

- `recheck` (`makenowjust/recheck`) for detecting dangerous regexes
- `safe-regex` for static determination

---

## SESS

### Cookie / Session

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `res.cookie(name, value, options)` | Express native | `options.httpOnly` / `options.secure` / `options.sameSite` / `options.maxAge` | in production: `httpOnly=true`, `secure=true`, `sameSite=strict/lax` |
| `req.session.userId = userInput` | `express-session` | session field assignment | store trusted identifiers only; avoid storing sensitive information |
| `req.session.destroy()` | `express-session` | call timing | destroy at logout / exceptions |
| `cookieSession()` | `cookie-session` | signing key `keys` | strong keys; `signed=true` |

### JWT

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `jwt.sign(payload, secretOrPrivateKey, options)` | `jsonwebtoken` | `options.algorithm` / key source | pin `algorithm`; HS256/RS256 explicitly specified |
| `jwt.verify(token, secretOrPublicKey, options)` | `jsonwebtoken` | `options.algorithms` whitelist | explicit `algorithms: ['HS256']`; disable `none` |
| `jwt.decode(token, { complete: true })` | `jsonwebtoken` | decodes only without verification; must not be used for authorization | must be distinguished from `verify` |
| `new SignJWT(payload).setProtectedHeader(...).sign(key)` | `jose` | header alg | pin the algorithm |
| `jwtVerify(token, secret, options)` | `jose` | `options.algorithms` | whitelist |

---

## CRYPTO

### Weak Hashing/Encryption

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `crypto.createHash('md5')` | native `crypto` | algorithm name | use `sha256` / `sha512`; forbid md5/sha1 in security contexts |
| `crypto.createHash('sha1')` | native `crypto` | algorithm name | same as above |
| `md5(userInput)` | `md5` / `crypto-js` | algorithm name | same as above |
| `crypto.createCipher(algorithm, password)` | native `crypto` (deprecated) | algorithm name | use `createCipheriv` + random IV |
| `crypto.createDecipher(algorithm, password)` | native `crypto` (deprecated) | algorithm name | same as above |

### Randomness / Keys

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `Math.random()` | native | return value used for tokens / verification codes | use `crypto.randomBytes` / `crypto.randomUUID` |
| `crypto.randomBytes(size)` | native | generation length | used for IV / nonce / token; sufficient length |
| `crypto.pbkdf2Sync(password, salt, iterations, keylen, digest)` | native | `iterations` / `digest` | iterations ≥ 100k; use `sha512` |
| `crypto.scryptSync(password, salt, keylen)` | native | parameters | recommended for password derivation |
| hardcoded keys outside `process.env.SECRET` | business code | key string | use KMS / Vault; committing forbidden |

---

## CSRF

### Missing Protection Mechanisms

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `app.use(csrf())` not mounted | `csurf` | global / route-level middleware | mount on all state-changing routes |
| `csurf({ cookie: { ... } })` | `csurf` | `cookie` configuration | prefer session-stored tokens |
| `app.post('/action', handler)` without csrf validation | Express native | route registration | combine `csurf` + template-injected `req.csrfToken()` |
| `app.use(cors({ credentials: true, origin: '*' }))` | `cors` | `origin` configuration | disable the wildcard + credentials combination |

### Bypass Scenarios

- Content-Type `text/plain` / `application/x-www-form-urlencoded` does not trigger CORS preflight
- Subdomain cookie injection overriding the csrf token
- SameSite=None without Secure causing cross-site cookie sending

---

## CFG

### CORS

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `app.use(cors({ origin: '*' }))` | `cors` | `origin` | explicit origin whitelist |
| `cors({ credentials: true, origin: true })` | `cors` | `origin` callback | forbid reflecting origin + credentials |
| `res.setHeader('Access-Control-Allow-Origin', userOrigin)` | native | header value | whitelist |

### Security Headers

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `app.use(helmet())` | `helmet` | default configuration | enable defaults in production |
| `helmet({ contentSecurityPolicy: false })` | `helmet` | CSP disabled | configure CSP explicitly |
| `res.setHeader('X-Frame-Options', 'DENY')` | native | header value | DENY/SAMEORIGIN by default |

### Debug / Errors

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `app.use(errorhandler())` | `errorhandler` | development only | disable detailed stacks in production |
| `res.status(500).send(err.stack)` | business code | 1st argument | return only error codes in production |
| `NODE_ENV !== 'production'` branch exposing debug endpoints | business code | environment variable | deployment checks; CI validation |

### Dependencies / Environment

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `require(userControlledModule)` | native | 1st argument | forbid user-controlled module paths |
| `process.env[userInput]` | native | property name | avoid user input accessing arbitrary env vars |
| `dotenv.config({ path: userPath })` | `dotenv` | `path` | fixed path; user control forbidden |

---

## EXPORT

### Exporters

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `worksheet.addRow(userValues)` | `exceljs` | `userValues` cell values | neutralize formula prefixes (prefix `'`); force text format |
| `stringify(records)` / `stringifier.write(row)` | `csv-stringify`, `fast-csv` | record field values | formula character detection and neutralization before writing |
| `new Parser().parse(data)` | `json2csv` | field values | same as above |
| handwritten `` `${v1},${v2}` `` CSV concatenation | none | concatenated fields | same as above |

### Formula Injection Patterns

- Cell values starting with `=` `+` `-` `@` interpreted by spreadsheets as formulas
- DDE payloads and HYPERLINK phishing chains (same mechanism as the dotnet side)

---

## PROMPT

### Prompt Assembly and RAG

| Sink API | Package | Controllable Parameter Position | Reference Barrier |
| --- | --- | --- | --- |
| `ChatPromptTemplate.fromMessages([...userContent])` | `langchain` | userContent roles / content | separate instructions from data; sanitize inputs |
| `openai.chat.completions.create({ messages })` | `openai` | any role slot in messages | the system role must not be overwritable by data |
| `streamText({ prompt, tools })` | `ai` (Vercel AI SDK) | prompt / tool definitions | minimize tool permissions; human confirmation gate on output |
| vector retrieval results concatenated directly into the prompt | `langchain` vectorstores | retrieved document content | treat retrieved content as data; cite sources |

### Tool/Function Calls (Including MCP)

- Tool permission scope larger than the task requires; MCP tools executing without confirmation
- LLM output JSON parsed by `JSON.parse` and directly driving downstream actions
