gs4_cisplatin <- function(df, type="prob", 
                          p_threshold = 0.5, 
                          unmeasured_genes = c("SLC25A45", "TMC4", "MALAT1")){
    # this function implements a logistic regression model for predicting 
    # drug response for cisplatin based chemotherapy 
    # the model was built using a pan-cancer approach. 
    # data.frame df: gene expression data.frame with genes as columns
    # numeric p_threshold: probability threshold for prediction
    # vector unsmeasured_genes: provide a vector of unmeasured genes to be removed
    #                           this is equivalent to imputing 0 for the GE.
    # We miss the following genes in our data: 17 - SLC25A45, 19 - TMC4, 21 - MALAT1
    # change to NULL if all genes are measured
    # reference: 
    # J. D. Wells et al. 2021 DOI:10.1177/11769351211002494
    # "Pan-Cancer Transcriptional Models Predicting Chemosensitivity in Human Tumors"

    # betas coefficients from GLM elastic net
    gs4 <- data.frame(Symbol = c('SLFN11', 'TASOR', 'DDX50', 'BCAT1', 
                                 'SALL4', 'PDLIM4', 'METAP2', 
                                'LRRC8C', 'QKI', 'STOML2', 'SLC35A2', 
                                'NEBL', 'ABHD11', 'CALCOCO1', 'ZNF91', 
                                'ZDHHC9', 'SLC25A45', 'MYO5B', 'TMC4', 
                                'TFF3', 'BSPRY', 'CNPPD1', 'CLDN3', 'BSPRY'),
                      B = c(0.07806286, 0.0584335, 0.055776578, 0.029278636, 
                      0.025196954, 0.021625076, 0.020362816, 0.012095118,
                      0.008967228, 0.001460649, -0.002316639, -0.002369246, 
                      -0.003712791, -0.007393136, -0.009960618, -0.01652152,
                      -0.023694588, -0.034605258, -0.040749427, -0.044766622,
                      -0.056125044, -0.056762982, -0.125547451, -0.146640606))

    # if unmeasured genes are provided as a vector
    # we remove them from the predictor
    if ( is.vector(unmeasured_genes)) {
        for ( gene in unmeasured_genes) {
           gs4 <- gs4[!(gs4["Symbol"]==gene), ]
        }
    }

    linear_predictor <- rep(0.0, nrow(df))
    for (model_term in 1:nrow(gs4)) {
    linear_predictor <- linear_predictor +
        df[, gs4[[model_term, "Symbol"]]] * gs4[[model_term, "B"]]
    
    }
    
    # logistic function
    # p(x) = 1/( 1 + exp(-(beta_0 + beta_1 * x_1 + ... + beta_n * x_n)))
    probability <-  1/(1+exp(-linear_predictor[[1]]))
        
    if ( type == "prob"){
        results <- probability
    } else if (type == "class") {
        results <- ifelse(probability>=p_threshold, 1, 0)
    }
    
    return(results)
}


