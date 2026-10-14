// Two-table structured condenser solver.
// Each code = syllable A (first half, table 0) + syllable B (second half, table NTAB-1).
// A table: major (0 = consonant-major, value = LW*p + r ; 1 = vowel-major, value = CW*r + p), consonant order p, vowel order r,
// serpentine flag (reverse the minor index on odd major rows), offset (mod 100). Cells >= LIMIT are invalid.
// usage: june_sa2 job out restarts iters seed threads
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <map>
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
static std::string consAlpha, vowAlpha;
static int NTAB = 2, LW = 6, CW = 20, LIMIT = 100, ADD = 0;
static int MAJ[2] = {-1, -1};   // -1 = free (annealed), 0 cons-major, 1 vowel-major
static int SHARE_ORDERS = 0;    // 1: both tables share consonant & vowel orders (differ only in major/serp/offset)
struct Tab { int major = 0, serp = 0, off = 0; std::vector<int> cpos, vrank; };
struct State { Tab t[2]; std::vector<int> v0, v1; };
static int NC, NV, NT;
static void vals(const Tab& T, std::vector<int>& out) {
    out.resize(NT);
    for (int i = 0; i < NT; i++) {
        int p = T.cpos[tcons[i]], r = T.vrank[tvow[i]], cell;
        if (T.major == 0) { if (T.serp && (p & 1)) r = LW - 1 - r; cell = LW * p + r; if (r >= LW) { out[i] = -1; continue; } }
        else { if (T.serp && (r & 1)) p = CW - 1 - p; cell = CW * r + p; if (p >= CW || p < 0) { out[i] = -1; continue; } }
        out[i] = cell >= LIMIT ? -1 : (cell + T.off) % 100;
    }
}
static void allVals(State& s) {
    if (SHARE_ORDERS) { s.t[1].cpos = s.t[0].cpos; s.t[1].vrank = s.t[0].vrank; }
    vals(s.t[0], s.v0);
    if (NTAB == 2) vals(s.t[1], s.v1); else s.v1 = s.v0;
}
static double score(const State& s, std::vector<int>& cv) {
    double S = 0;
    for (size_t i = 0; i < codes.size(); i++) {
        int a = s.v0[codes[i].a], b = s.v1[codes[i].b];
        cv[i] = (a < 0 || b < 0) ? -1 : (a * 100 + b + ADD) % 10000;
    }
    for (size_t i = 0; i < codes.size(); i++) {
        if (cv[i] < 0) { S -= 6.0; continue; }
        S += UNI[cv[i]] - REF; int p = codes[i].prev; if (p >= 0 && cv[p] >= 0) S += bonus(cv[p], cv[i]);
    }
    return S;
}
int main(int argc, char** argv) {
    if (argc < 7) { fprintf(stderr, "usage: job out restarts iters seed threads\n"); return 1; }
    int restarts = atoi(argv[3]); long iters = atol(argv[4]); unsigned seed = (unsigned)atol(argv[5]); int threads = atoi(argv[6]);
    std::ifstream in(argv[1]); std::string line, lmdir; std::map<std::string, int> tid; double T0 = 20, T1 = 1;
    std::vector<std::vector<int>> msgs;
    auto T = [&](const std::string& u) { auto it = tid.find(u); if (it != tid.end()) return it->second; int k = (int)tname.size(); tid[u] = k; tname.push_back(u); return k; };
    while (std::getline(in, line)) {
        std::istringstream ss(line); std::string tag; ss >> tag;
        if (tag == "LM") ss >> lmdir; else if (tag == "NTAB") ss >> NTAB; else if (tag == "LW") ss >> LW; else if (tag == "CW") ss >> CW;
        else if (tag == "LIMIT") ss >> LIMIT; else if (tag == "ADD") ss >> ADD; else if (tag == "TEMP") ss >> T0 >> T1;
        else if (tag == "MAJ") ss >> MAJ[0] >> MAJ[1]; else if (tag == "SHARE") ss >> SHARE_ORDERS;
        else if (tag == "MSG") { std::string n, u; ss >> n; std::vector<int> m; while (ss >> u) m.push_back(u == "--" ? -1 : T(u)); msgs.push_back(m); }
    }
    load_lm(lmdir); NT = (int)tname.size();
    for (int t = 0; t < NT; t++) {
        size_t p = consAlpha.find(tname[t][0]); if (p == std::string::npos) { p = consAlpha.size(); consAlpha += tname[t][0]; } tcons.push_back((int)p);
        size_t q = vowAlpha.find(tname[t][1]); if (q == std::string::npos) { q = vowAlpha.size(); vowAlpha += tname[t][1]; } tvow.push_back((int)q);
    }
    NC = (int)consAlpha.size(); NV = (int)vowAlpha.size();
    for (auto& m : msgs) { int last = -1; for (size_t i = 0; i + 1 < m.size(); i += 2) { if (m[i] < 0 || m[i + 1] < 0) { last = -1; continue; } codes.push_back({m[i], m[i + 1], last}); last = (int)codes.size() - 1; } }
    fprintf(stderr, "ntab=%d types=%d cons=%d(%s) vows=%d(%s) codes=%zu LW=%d CW=%d\n", NTAB, NT, NC, consAlpha.c_str(), NV, vowAlpha.c_str(), codes.size(), LW, CW);
    // consonant positions range: cons-major uses 0..NCP-1 where NCP = max(NC, ceil(LIMIT/LW)); vowel-major needs p < CW
    int NCP = std::max(NC, std::max(CW, (LIMIT + LW - 1) / LW)), NVP = std::max(NV, std::max(LW, (LIMIT + CW - 1) / CW));
    struct Res { double s; State st; }; std::vector<Res> res(restarts); std::atomic<int> nxt(0);
    auto worker = [&]() {
        std::vector<int> cv(codes.size());
        for (;;) {
            int r = nxt.fetch_add(1); if (r >= restarts) break;
            std::mt19937_64 rng(seed * 1000003ull + r); std::uniform_real_distribution<double> U(0, 1);
            State s;
            for (int k = 0; k < 2; k++) {
                Tab& t = s.t[k];
                std::vector<int> cp(NCP); for (int i = 0; i < NCP; i++) cp[i] = i; std::shuffle(cp.begin(), cp.end(), rng); t.cpos.assign(cp.begin(), cp.begin() + NC);
                std::vector<int> vp(NVP); for (int i = 0; i < NVP; i++) vp[i] = i; std::shuffle(vp.begin(), vp.end(), rng); t.vrank.assign(vp.begin(), vp.begin() + NV);
                t.major = MAJ[k] >= 0 ? MAJ[k] : (int)(rng() & 1); t.serp = rng() & 1; t.off = rng() % 100;
            }
            allVals(s); double S = score(s, cv); State best = s; double bs = S;
            // position pools allow moving a consonant/vowel into an unused slot
            for (long it = 0; it < iters; it++) {
                double Tm = T0 * pow(T1 / T0, (double)it / iters);
                State n = s; int k = (NTAB == 2 && !SHARE_ORDERS) ? (int)(rng() & 1) : 0; Tab& t = n.t[k];
                double m = U(rng);
                if (m < 0.45) { int a = rng() % NC; int np = rng() % NCP; int owner = -1; for (int c = 0; c < NC; c++) if (t.cpos[c] == np) owner = c; if (owner >= 0) std::swap(t.cpos[a], t.cpos[owner]); else t.cpos[a] = np; }
                else if (m < 0.65) { int a = rng() % NV; int np = rng() % NVP; int owner = -1; for (int v = 0; v < NV; v++) if (t.vrank[v] == np) owner = v; if (owner >= 0) std::swap(t.vrank[a], t.vrank[owner]); else t.vrank[a] = np; }
                else if (m < 0.72) { int kk = (NTAB == 2) ? (int)(rng() & 1) : 0; n.t[kk].serp ^= 1; }
                else if (m < 0.76) { int kk = (NTAB == 2) ? (int)(rng() & 1) : 0; if (MAJ[kk] < 0) n.t[kk].major ^= 1; }
                else if (m < 0.90) { int kk = (NTAB == 2) ? (int)(rng() & 1) : 0; n.t[kk].off = (n.t[kk].off + (rng() % 2 ? 1 : 99)) % 100; }
                else { int kk = (NTAB == 2) ? (int)(rng() & 1) : 0; n.t[kk].off = rng() % 100; }
                allVals(n); double NS = score(n, cv);
                if (NS >= S || U(rng) < exp((NS - S) / Tm)) { s = n; S = NS; if (S > bs) { bs = S; best = s; } }
            }
            res[r] = {bs, best};
        }
    };
    std::vector<std::thread> th; for (int i = 0; i < threads; i++) th.emplace_back(worker); for (auto& x : th) x.join();
    std::sort(res.begin(), res.end(), [](const Res& a, const Res& b) { return a.s > b.s; });
    FILE* o = fopen(argv[2], "w"); std::vector<int> cv(codes.size());
    for (int r = 0; r < restarts; r++) {
        State& s = res[r].st; allVals(s); score(s, cv);
        fprintf(o, "R %d %.3f %.4f", r, res[r].s, res[r].s / codes.size());
        for (int k = 0; k < NTAB; k++) {
            const Tab& t = s.t[k]; std::vector<std::pair<int,char>> co, vo;
            for (int c = 0; c < NC; c++) co.push_back({t.cpos[c], consAlpha[c]}); for (int v = 0; v < NV; v++) vo.push_back({t.vrank[v], vowAlpha[v]});
            std::sort(co.begin(), co.end()); std::sort(vo.begin(), vo.end());
            std::string cs, vs; for (auto& x : co) { cs += x.second; } for (auto& x : vo) { vs += x.second; vs += char('0' + x.first); }
            fprintf(o, " | T%d maj=%d serp=%d off=%d cons=%s vow=%s", k, t.major, t.serp, t.off, cs.c_str(), vs.c_str());
        }
        fprintf(o, "\nCODES"); for (size_t i = 0; i < codes.size(); i++) fprintf(o, " %04d", cv[i] < 0 ? 9999 : cv[i]); fprintf(o, "\n");
    }
    fclose(o); fprintf(stderr, "best %.3f (%.4f/code)\n", res[0].s, res[0].s / codes.size());
}
