PROG = corpusextract.py
INDIR = test
OUTDIR = test/out

test:
	OPS = --debug -s

	@echo ##################################################
	@echo # Test 1: Simple uncoded file
	@echo ##################################################
	$PROG $OPS NP* $(INDIR)/simple.psd -o $(OUTDIR)/test1_out.txt
