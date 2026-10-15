# Node.js Audit Grabber Index

This file unifies the search keywords, priority enumeration targets, and common landing points for node-* skills, reducing divergence during the enumeration phase. It is a peer of shared/DOTNET_AUDIT_GRABBER_INDEX.md — same methodology, different ecosystem keywords.

## Usage Rules

- Search with this index by the five layers: entry definition, binding & parameters, precondition controls, sensitive operations, security configuration
- Search exact API / framework decorators / middleware names first, then project-internal wrapper names, infrastructure directories, utility functions, and registration code
- Each skill's "Enumeration Rules (Mandatory Refinement)" must at least cover the keywords, object types, and record fields corresponding to this index
- If the project has secondary encapsulation, the wrapper names must be appended back into this skill's output, forming a project-internal private grabber table
- `node_modules/`, `dist/`, `build/`, `.next/`, `.nuxt/`, and `coverage` directories are excluded by default and not part of the audit surface; lockfiles (package-lock.json / yarn.lock / pnpm-lock.yaml) are an exception and must be included in the supply chain audit

## Entry Definition Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Generic Node | http.createServer, createServer, req.url, req.method | Native route dispatch, method determination |
| Express | express(), Router(), app.get, app.post, app.put, app.delete, app.patch, app.all, app.use, router.use | Route template, HTTP method, mount prefix, middleware chain |
| NestJS | @Controller, @Get, @Post, @Put, @Delete, @Patch, @All, @UseGuards, @UseInterceptors | Decorator routes, Guard/Interceptor coverage |
| Next.js | app/api/**/route.{js,ts}, pages/api/**, export function GET, export function POST, NextRequest, middleware.ts | File-convention routes, HTTP method exports, edge middleware |
| Koa | new Koa(), koa-router, router.get, router.post, app.use | Routes, ctx passing |
| Fastify | fastify.route, fastify.get, fastify.post, fastify.register, addHook | Route registration, plugin scoping, hooks |
| Nuxt/Nitro | defineEventHandler, getQuery, readBody, server/api/** | Server entries, parameter reads |

## Binding & Parameter Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Express family | req.params, req.query, req.body, req.headers, req.cookies | Parameter sources, name mapping |
| Koa family | ctx.params, ctx.query, ctx.request.body, ctx.headers, ctx.cookies | Same as above |
| NestJS | @Body(), @Query(), @Param(), @Headers(), ValidationPipe | DTO expanded fields, validation pipe whitelist |
| Next/Nuxt | await request.json(), request.nextUrl.searchParams, getQuery(), readBody(), getRouterParam() | Parameter sources |
| File input | multer, busboy, formidable, multipart | File name, dest, limits |

## Precondition Control Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Middleware chains | app.use, router.use, next(), Express middleware ordering | Mount order, short-circuit conditions |
| Auth middleware | passport.authenticate, express-jwt, expressjwt, jwt.verify, express-session, cookie-session, next-auth, getServerSession | Auth coverage scope, global/route-level |
| NestJS control plane | @UseGuards, AuthGuard, CanActivate, @Public | Guard coverage, anonymous allowances |
| Security headers / CORS | helmet, cors(, Access-Control-Allow, CSP | Global configuration points |

## Sensitive Operation Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| CMD | child_process, exec(, execSync(, spawn(, execFile(, shell: true | Command construction, shell involvement |
| SQL | mysql, mysql2, pg, .query(, knex.raw, sequelize.query, typeorm | Query sources, concatenated fragments |
| NoSQL | mongoose, mongodb, .find(, $where, $regex, $gt | Query object sources, operator-injectable fields |
| SSRF | axios., fetch(, got(, request(, undici, http.get, https.get | URL sources, redirect following |
| File | fs.readFile, fs.writeFile, fs.createReadStream, fs.createWriteStream, path.join, path.resolve, res.sendFile | Path sources, normalization |
| Template | ejs, pug, nunjucks, handlebars, mustache, res.render, .compile( | Template sources, concatenation, template name controllability |
| Expression / deserialization | eval(, new Function(, vm.runIn, node-serialize, unserialize, yaml.load | Execution context, input sources |
| Crypto | crypto.createHash, md5, sha1, createCipher(deprecated), Math.random(used for tokens) | Weak algorithms, randomness sources |
| JWT / session | jsonwebtoken, jwt.sign, jwt.verify, jose | Algorithm pinning, key sources |
| Archive extraction | adm-zip, extract-zip, tar, unzipper, yauzl | Extraction landing points, Zip Slip |

## Security Configuration Grabbers

| Type | Priority Keywords | Key Records |
| ---- | ---- | ---- |
| Dependency manifests | package.json, package-lock.json, yarn.lock, pnpm-lock.yaml | Dependency versions, script hooks, git/http protocol dependencies |
| Environment variables | process.env, dotenv, .env | Hardcoded secrets, env files committed to the repo |
| Debug / errors | NODE_ENV, app.get('env'), error.stack, console.log(sensitive) | Error leakage, debug switches |
