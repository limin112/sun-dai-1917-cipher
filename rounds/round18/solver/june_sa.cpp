// Simulated-annealing solver for syllable-condenser tables (two syllables -> one 4-digit Chinese telegraph code).
// Models:
//   free  : every syllable type -> distinct value 00..99 (injective)
//   coord : consonant -> tens digit, syllable -> units digit; collisions penalised
//   lin   : value = (W*pos(cons) + rank(vowel) [reversed on odd pos if serp] + off) mod 100 ; cells >= LIMIT invalid
// Scoring: per code  uni[code]-REF  + bigram bonus with previous code (Dudout lm3 format).
// usage: june_sa job.txt out.txt restarts iters seed threads
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <mutex>
#include <random>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

static float UNI[10000]; static double REF = 0; static float BDEF = 0.f;
static std::vector<uint32_t> HK; static std::vector<float> HV; static uint32_t HMASK;
static inline float bonus(int a, int b) {
    uint32_t k = (uint32_t)a * 10000u + (uint32_t)b + 1u, h = (k * 2654435761u) & HMASK;
    while (HK[h]) { if (HK[h] == k) return HV[h]; h = (h + 1) & HMASK; }
    return BDEF;
}
static void load_lm(const std::string& d) {
    FILE* f = fopen((d + "/uni.f32").c_str(), "rb"); if (!f || fread(UNI, 4, 10000, f) != 10000) exit(2); fclose(f);
    for (int i = 0; i < 10000; i++) REF += UNI[i]; REF /= 10000;
    { FILE* g = fopen((d + "/bidef.f32").c_str(), "rb"); if (g) { if (fread(&BDEF, 4, 1, g) != 1) BDEF = 0; fclose(g); } }
    f = fopen((d + "/bi.u32").c_str(), "rb"); fseek(f, 0, SEEK_END); long n = ftell(f) / 4; fseek(f, 0, SEEK_SET);
    std::vector<uint32_t> K(n); std::vector<float> V(n);
    if ((long)fread(K.data(), 4, n, f) != n) exit(2); fclose(f);
    f = fopen((d + "/bi.f32").c_str(), "rb"); if ((long)fread(V.data(), 4, n, f) != n) exit(2); fclose(f);
    uint32_t cap = 1; while (cap < 4 * (uint32_t)n) cap <<= 1; HK.assign(cap, 0); HV.assign(cap, 0); HMASK = cap - 1;
    for (long i = 0; i < n; i++) { uint32_t k = K[i] + 1u, h = (k * 2654435761u) & HMASK; while (HK[h]) h = (h + 1) & HMASK; HK[h] = k; HV[h] = V[i]; }
}

struct Code { int a, b, prev; };
static std::vector<Code> codes; static std::vector<std::string> tname; static std::vector<int> tcons, tvow;
static std::string consAlpha, vowAlpha; static std::string MODEL = "free";
static int LW = 6, LIMIT = 100; static double CPEN = 3.0; static int ADD = 0; static int ARR[4] = {0,1,2,3}; static int FREEADD2 = 0, DIGADD = 0;  // lin: row width, valid cells; coord: collision penalty
static std::vector<std::pair<int,int>> anchors;  // type -> value (hard)
static std::vector<std::string> mnames; static std::vector<std::vector<int>> msgs;

struct State {
    std::vector<int> val;      // per type, -1 invalid
    // coord
    std::vector<int> tens, unit;
    // lin
    std::vector<int> cpos, vrank; int serp = 0, off = 0, al = 0, add2 = 0;
    int U[2][8];
};

static inline int codeval(const State& s, const Code& c) {
    int va = s.val[c.a], vb = s.val[c.b];
    if (va < 0 || vb < 0) return -1;
    if (DIGADD) { // digit-wise additive on second half digits (mod 10 each)
        vb = ((vb / 10 + s.add2 / 10) % 10) * 10 + (vb % 10 + s.add2 % 10) % 10;
    } else vb = (vb + s.add2) % 100;
    int d[4] = {va / 10, va % 10, vb / 10, vb % 10};
    int code = d[ARR[0]] * 1000 + d[ARR[1]] * 100 + d[ARR[2]] * 10 + d[ARR[3]];
    return (code + ADD) % 10000;
}
static double scoreAll(const State& s, std::vector<int>& cv) {
    double S = 0;
    for (size_t i = 0; i < codes.size(); i++) cv[i] = codeval(s, codes[i]);
    for (size_t i = 0; i < codes.size(); i++) {
        if (cv[i] < 0) { S -= 6.0; continue; }
        S += UNI[cv[i]] - REF;
        int p = codes[i].prev; if (p >= 0 && cv[p] >= 0) S += bonus(cv[p], cv[i]);
    }
    return S;
}
static void linVals(State& s) {
    for (size_t t = 0; t < tname.size(); t++) {
        int p = s.cpos[tcons[t]], r = s.vrank[tvow[t]];
        if (r >= LW) r = s.al;
        if (s.serp && (p & 1)) r = LW - 1 - r;
        int cell = LW * p + r;
        if (cell >= LIMIT) { s.val[t] = -1; continue; }
        s.val[t] = (cell + s.off) % 100;
    }
}
static double coordPenalty(const State& s) {
    int cnt[100] = {0}; double P = 0;
    for (size_t t = 0; t < tname.size(); t++) { int v = s.val[t]; if (v >= 0) { if (cnt[v]) P += CPEN; cnt[v]++; } }
    return P;
}
static void coord2Vals(State& s) {
    for (size_t t = 0; t < tname.size(); t++) { int p = s.cpos[tcons[t]]; s.val[t] = p >= 20 ? -1 : 10 * (p / 2) + s.U[p % 2][tvow[t]]; }
}
static void coordVals(State& s) { for (size_t t = 0; t < tname.size(); t++) s.val[t] = 10 * s.tens[tcons[t]] + s.unit[t]; }
static bool anchorsOk(const State& s) { for (auto& a : anchors) if (s.val[a.first] != a.second) return false; return true; }

int main(int argc, char** argv) {
    if (argc < 7) { fprintf(stderr, "usage: job out restarts iters seed threads\n"); return 1; }
    int restarts = atoi(argv[3]); long iters = atol(argv[4]); unsigned seed = (unsigned)atol(argv[5]); int threads = atoi(argv[6]);
    std::ifstream in(argv[1]); std::string line, lmdir; std::map<std::string, int> tid;
    double T0 = 20.0, T1 = 1.0;
    auto T = [&](const std::string& u) { auto it = tid.find(u); if (it != tid.end()) return it->second; int k = (int)tname.size(); tid[u] = k; tname.push_back(u); return k; };
    while (std::getline(in, line)) {
        std::istringstream ss(line); std::string tag; ss >> tag;
        if (tag == "LM") ss >> lmdir;
        else if (tag == "MODEL") ss >> MODEL;
        else if (tag == "LW") ss >> LW;
        else if (tag == "LIMIT") ss >> LIMIT;
        else if (tag == "CPEN") ss >> CPEN;
        else if (tag == "ADD") ss >> ADD;
        else if (tag == "ARR") { std::string a; ss >> a; for (int i = 0; i < 4; i++) ARR[i] = a[i] - '1'; }
        else if (tag == "FREEADD2") ss >> FREEADD2;
        else if (tag == "DIGADD") ss >> DIGADD;
        else if (tag == "TEMP") ss >> T0 >> T1;
        else if (tag == "MSG") { std::string n, u; ss >> n; std::vector<int> m; while (ss >> u) m.push_back(u == "--" ? -1 : T(u)); msgs.push_back(m); mnames.push_back(n); }
        else if (tag == "ANCHOR") { std::string u; int v; ss >> u >> v; anchors.push_back({T(u), v}); }
    }
    load_lm(lmdir);
    int NT = (int)tname.size();
    for (int t = 0; t < NT; t++) {
        size_t p = consAlpha.find(tname[t][0]); if (p == std::string::npos) { p = consAlpha.size(); consAlpha += tname[t][0]; } tcons.push_back((int)p);
        size_t q = vowAlpha.find(tname[t][1]); if (q == std::string::npos) { q = vowAlpha.size(); vowAlpha += tname[t][1]; } tvow.push_back((int)q);
    }
    int NC = (int)consAlpha.size(), NV = (int)vowAlpha.size();
    for (size_t mi = 0; mi < msgs.size(); mi++) {
        int last = -1; auto& m = msgs[mi];
        for (size_t i = 0; i + 1 < m.size(); i += 2) {
            if (m[i] < 0 || m[i + 1] < 0) { last = -1; continue; }
            codes.push_back({m[i], m[i + 1], last}); last = (int)codes.size() - 1;
        }
    }
    fprintf(stderr, "model=%s types=%d cons=%d(%s) vows=%d(%s) codes=%zu anchors=%zu\n", MODEL.c_str(), NT, NC, consAlpha.c_str(), NV, vowAlpha.c_str(), codes.size(), anchors.size());
    struct Res { double score; State s; };
    std::vector<Res> res(restarts); std::atomic<int> next(0);
    auto worker = [&]() {
        std::vector<int> cv(codes.size());
        for (;;) {
            int r = next.fetch_add(1); if (r >= restarts) break;
            std::mt19937_64 rng(seed * 1000003ull + r); std::uniform_real_distribution<double> U(0, 1);
            State s; s.val.assign(NT, -1);
            if (MODEL == "free") {
                std::vector<int> vals(100); for (int i = 0; i < 100; i++) vals[i] = i; std::shuffle(vals.begin(), vals.end(), rng);
                for (int t = 0; t < NT; t++) s.val[t] = vals[t];
                for (auto& a : anchors) { int owner = -1; for (int t = 0; t < NT; t++) if (s.val[t] == a.second) owner = t; if (owner >= 0) std::swap(s.val[owner], s.val[a.first]); else s.val[a.first] = a.second; }
            } else if (MODEL == "coord2") {
                std::vector<int> pos(std::max(20, NC)); for (size_t i = 0; i < pos.size(); i++) pos[i] = (int)i; std::shuffle(pos.begin(), pos.end(), rng);
                s.cpos.assign(pos.begin(), pos.begin() + NC);
                for (int a = 0; a < 2; a++) { std::vector<int> u(10); for (int i = 0; i < 10; i++) u[i] = i; std::shuffle(u.begin(), u.end(), rng); for (int v = 0; v < NV; v++) s.U[a][v] = v < 10 ? u[v] : rng() % 10; }
                coord2Vals(s);
            } else if (MODEL == "coord") {
                s.tens.resize(NC); s.unit.resize(NT);
                for (int c = 0; c < NC; c++) s.tens[c] = rng() % 10;
                for (int t = 0; t < NT; t++) s.unit[t] = rng() % 10;
                coordVals(s);
            } else {
                s.cpos.resize(NC); for (int c = 0; c < NC; c++) s.cpos[c] = c; std::shuffle(s.cpos.begin(), s.cpos.end(), rng);
                s.vrank.resize(NV); for (int v = 0; v < NV; v++) s.vrank[v] = v; std::shuffle(s.vrank.begin(), s.vrank.end(), rng);
                s.al = rng() % LW;
                s.serp = rng() & 1; s.off = rng() % 100; linVals(s);
            }
            auto full = [&](const State& st) { double sc = scoreAll(st, cv); if (MODEL == "coord") sc -= coordPenalty(st);
                if (MODEL == "coord2") { int cov[10] = {0}; for (int a = 0; a < 2; a++) for (int v = 0; v < NV; v++) cov[st.U[a][v]] = 1; for (int u = 0; u < 10; u++) if (!cov[u]) sc -= CPEN; } if (!anchors.empty() && MODEL != "free" && !anchorsOk(st)) sc -= 50; return sc; };
            double S = full(s); State best = s; double bestS = S;
            for (long it = 0; it < iters; it++) {
                double Tm = T0 * pow(T1 / T0, (double)it / iters);
                State n = s;
                if (MODEL == "free") {
                    int t = rng() % NT; bool fixed = false; for (auto& a : anchors) if (a.first == t) fixed = true; if (fixed) continue;
                    int v = rng() % 100; int owner = -1; for (int u = 0; u < NT; u++) if (n.val[u] == v) owner = u;
                    if (owner >= 0) { bool f2 = false; for (auto& a : anchors) if (a.first == owner) f2 = true; if (f2) continue; std::swap(n.val[owner], n.val[t]); } else n.val[t] = v;
                } else if (MODEL == "coord2") {
                    double m = U(rng); int NP = std::max(20, NC);
                    if (m < 0.5) { int a = rng() % NC; int np = rng() % NP; int owner = -1; for (int c = 0; c < NC; c++) if (n.cpos[c] == np) owner = c; if (owner >= 0) std::swap(n.cpos[a], n.cpos[owner]); else n.cpos[a] = np; }
                    else if (m < 0.75) { int a = rng() % 2, v = rng() % NV; n.U[a][v] = rng() % 10; }
                    else { int a = rng() % 2, v = rng() % NV, w = rng() % NV; std::swap(n.U[a][v], n.U[a][w]); }
                    coord2Vals(n);
                } else if (MODEL == "coord") {
                    double m = U(rng);
                    if (m < 0.45) { int t = rng() % NT; n.unit[t] = rng() % 10; }
                    else if (m < 0.7) { int a = rng() % NT, b = rng() % NT; std::swap(n.unit[a], n.unit[b]); }
                    else if (m < 0.85) { int c = rng() % NC; n.tens[c] = rng() % 10; }
                    else { int a = rng() % NC, b = rng() % NC; std::swap(n.tens[a], n.tens[b]); }
                    coordVals(n);
                } else {
                    double m = U(rng);
                    if (m < 0.55) { int a = rng() % NC, b = rng() % NC; std::swap(n.cpos[a], n.cpos[b]); }
                    else if (m < 0.70) { int a = rng() % NV, b = rng() % NV; std::swap(n.vrank[a], n.vrank[b]); }
                    else if (m < 0.75) { n.al = rng() % LW; }
                    else if (m < 0.82) n.serp ^= 1;
                    else if (m < 0.88) n.off = (n.off + (rng() % 2 ? 1 : 99)) % 100;
                    else if (m < 0.92 || !FREEADD2) n.off = rng() % 100;
                    else if (m < 0.96) n.add2 = (n.add2 + (rng() % 2 ? 1 : 99)) % 100;
                    else n.add2 = rng() % 100;
                    linVals(n);
                }
                double NS = full(n);
                if (NS >= S || U(rng) < exp((NS - S) / Tm)) { s = n; S = NS; if (S > bestS) { bestS = S; best = s; } }
            }
            res[r] = {bestS, best};
        }
    };
    std::vector<std::thread> th; for (int i = 0; i < threads; i++) th.emplace_back(worker); for (auto& t : th) t.join();
    std::sort(res.begin(), res.end(), [](const Res& a, const Res& b) { return a.score > b.score; });
    FILE* o = fopen(argv[2], "w");
    std::vector<int> cv(codes.size());
    for (int r = 0; r < restarts; r++) {
        const State& s = res[r].s; scoreAll(s, cv);
        int nvalid = 0; for (int x : cv) if (x >= 0) nvalid++;
        fprintf(o, "R %d %.3f %.4f", r, res[r].score, res[r].score / std::max(1, (int)codes.size()));
        if (MODEL == "coord2") { std::string co(std::max(20, NC), '.'); for (int c = 0; c < NC; c++) co[s.cpos[c]] = consAlpha[c]; fprintf(o, " pos=%s U0=", co.c_str()); for (int v = 0; v < NV; v++) fprintf(o, "%c%d", vowAlpha[v], s.U[0][v]); fprintf(o, " U1="); for (int v = 0; v < NV; v++) fprintf(o, "%c%d", vowAlpha[v], s.U[1][v]); }
        if (MODEL == "lin") { std::string co(NC, '?'); for (int c = 0; c < NC; c++) co[s.cpos[c]] = consAlpha[c]; std::string vo; for (int v = 0; v < NV; v++) { vo += vowAlpha[v]; vo += char('0' + (s.vrank[v] < LW ? s.vrank[v] : 10 + s.al)); } fprintf(o, " cons=%s vow=%s serp=%d off=%d add2=%d", co.c_str(), vo.c_str(), s.serp, s.off, s.add2); }
        fprintf(o, "\nTABLE");
        for (int t = 0; t < NT; t++) fprintf(o, " %s=%d", tname[t].c_str(), s.val[t]);
        fprintf(o, "\nCODES");
        for (size_t i = 0; i < codes.size(); i++) fprintf(o, " %04d", cv[i] < 0 ? 9999 : cv[i]);
        fprintf(o, "\n");
    }
    fclose(o);
    fprintf(stderr, "best %.3f (%.4f/code)\n", res[0].score, res[0].score / codes.size());
}
