* ------------------------------------------------
* Standalone MACC parameter extractor for RICE50+
* ------------------------------------------------

$setglobal datapath    "RICE50xmodel/data_ed58/"
$setglobal pback       550
$setglobal gback       0.025
$setglobal expcost2    2.8
$setglobal tstart_pbtransition  7
$setglobal tend_pbtransition    28
$setglobal klogistic   0.25

* --- SETS ---
SET t;
ALIAS(t, tp1);
SET pre(t,tp1);
SET n /
    arg, aus, aut, bel, bgr, blt, bra, can, chl, chn, cor, cro,
    dnk, egy, esp, fin, fra, gbr, golf57, grc, hun, idn, irl, ita,
    jpn, meme, mex, mys, nde, nld, noan, noap, nor, oeu, osea, pol,
    prt, rcam, rcz, rfa, ris, rjan57, rom, rsaf, rsam, rsas, rsl,
    rus, sau, slo, sui, swe, tha, tur, ukr, usa, vnm, zaf /;

SET sector 'EnerData sectors' /
    "Electricity"
    "Other_energy_transformation"
    "Total_buildings_agriculture"
    "Total_industry_processes"
    "Total_industry_fuelcombustion"
    "Total_CO2"
    "Total_transport" /;
SET quant  'AR6 quantiles' / "prob25","prob33","prob50","prob66","prob75" /;
SET coef   'Polynomial coefficients' / c0*c4 /;
SET ghg    'Greenhouse gases' / co2, ch4, n2o /;
SET coefact(coef,*) / c1.co2, c4.co2 /;

* --- TIME PARAMETERS (must be declared before include) ---
PARAMETER tperiod(t);
PARAMETER year(t);
PARAMETER tlen(t);
PARAMETER begyear(t);
PARAMETER preds(t,t);

$include '%datapath%time.inc'

* --- SCALAR PARAMETERS ---
PARAMETERS
    expcost2  / %expcost2% /
    pback     / %pback%    /
    gback     / %gback%    /
;

PARAMETER coefn(coef) / c0 0, c1 1, c2 2, c3 3, c4 4 /;


**********************************************
* ----------- MACC CALCULATIONS ---------------
**********************************************

* --- LOAD RAW DATA ---
PARAMETER macc_ed_coef(sector,*,t,n);
$gdxin '%datapath%data_mod_macc'
$load  macc_ed_coef
$gdxin

PARAMETER mx_correction_factor(sector,quant,t,n);
$gdxin '%datapath%data_mod_macc'
$load  mx_correction_factor
$gdxin

* --- COMPUTED PARAMETERS ---
PARAMETERS
    pbacktime(t)
    macc_coef(t,n,*,coef)
    mx(t,n,ghg)
    MXpback(t,n,ghg)
    MXstart(t,n,ghg)
    MXdiff(t,n,ghg)
    alpha(t)
;

* Map raw enerdata coefficients
macc_coef(t,n,'co2','c1') = macc_ed_coef('Total_CO2','a',t,n);
macc_coef(t,n,'co2','c4') = macc_ed_coef('Total_CO2','d',t,n);
macc_coef(t,n,'co2',coef)$(macc_coef(t,n,'co2',coef) < 0) = 0;

* Backstop price path
pbacktime(t) = pback * (1-gback)**(tperiod(t)-1);

* Logistic transition to backstop
SCALAR x0;
x0 = %tstart_pbtransition% + ((%tend_pbtransition%-%tstart_pbtransition%)/2);
alpha(t) = 1 / (1 + exp(-%klogistic% * (tperiod(t) - x0)));

* MX starting value (SSP2 default = prob50)
MXstart(t,n,'co2') = mx_correction_factor('Total_CO2','prob50',t,n);

* Backstop multiplier
MXpback(t,n,'co2')$(macc_ed_coef('Total_CO2','a',t,n) + macc_ed_coef('Total_CO2','d',t,n) > 0)
    = pbacktime(t) / (macc_ed_coef('Total_CO2','a',t,n) + macc_ed_coef('Total_CO2','d',t,n));

MXdiff(t,n,'co2') = max(MXstart(t,n,'co2') - MXpback(t,n,'co2'), 0);

* Final mx
mx(t,n,'co2') = MXstart(t,n,'co2') - alpha(t) * MXdiff(t,n,'co2');

* Apply mx to get final scaled coefficients
macc_coef(t,n,'co2','c1') = mx(t,n,'co2') * macc_ed_coef('Total_CO2','a',t,n);
macc_coef(t,n,'co2','c4') = mx(t,n,'co2') * macc_ed_coef('Total_CO2','d',t,n);


* --- OUTPUT ---
execute_unload 'output/data/macc_extract.gdx',
    macc_ed_coef,
    macc_coef,
    mx_correction_factor,
    mx,
    alpha,
    pbacktime,
    tperiod,
    year;

SET t_early(t) / 1, 2, 3 /;

FILE fout / 'output/data/macc_ed_early.csv' /;
PUT fout;
PUT '"sector","Dim2","t","n","Val"' /;

LOOP((t_early(t), n),
    PUT '"Total_CO2","a","' t.tl '","' n.tl '",' macc_ed_coef('Total_CO2','a',t,n):0:12 /;
    PUT '"Total_CO2","d","' t.tl '","' n.tl '",' macc_ed_coef('Total_CO2','d',t,n):0:12 /;
);

PUTCLOSE fout;



**********************************************
* ----------- BAU CALCULATIONS ---------------
**********************************************

*** * --- LOAD BASELINE DATA ---
*** SET ssp / SSP1, SSP2, SSP3, SSP4, SSP5 /;
*** SET ghg2 / co2, ch4, n2o /;
*** 
*** PARAMETER ssp_ci(ssp,t,n,ghg2);
*** PARAMETER ssp_ykali(ssp,t,n);
*** PARAMETER convq_ghg(ghg2) / co2 1, ch4 1e-3, n2o 1e-3 /;
*** 
*** $gdxin '%datapath%data_baseline'
*** $load ssp_ci
*** $load ssp_ykali
*** $gdxin
*** 
*** * --- COMPUTE EMI_BAU FOR SSP2, CO2, t=1,2,3 ---
*** PARAMETER emi_bau_early(t,n);
*** 
*** emi_bau_early(t_early,n) = convq_ghg('co2') 
***                           * ssp_ci('SSP2', t_early, n, 'co2') 
***                           * ssp_ykali('SSP2', t_early, n);
*** 
*** * --- WRITE TO CSV ---
*** FILE fout2 / 'output/data/emi_bau_early.csv' /;
*** PUT fout2;
*** PUT '"t","n","emi_bau_GtCO2yr"' /;
*** 
*** LOOP((t_early(t), n),
***     PUT '"' t.tl '","' n.tl '",' emi_bau_early(t,n):0:12 /;
*** );
*** 
*** PUTCLOSE fout2;
