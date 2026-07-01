from config import RANDOM_SEED
from sklearn.model_selection import StratifiedKFold, GridSearchCV


def tune_model(estimator, param_grid, X_trainval, y_trainval, seed=RANDOM_SEED, sample_weight = None, sample_weight_param = 'sample_weight'):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    grid = GridSearchCV(
            estimator=estimator,
            param_grid=param_grid,
            cv=skf,
            scoring='f1_macro',
            n_jobs=-1,
            refit=True,
        ) 
    fit_params = {}
    if sample_weight is not None:
        fit_params[sample_weight_param] = sample_weight
    
    grid.fit(X_trainval, y_trainval, **fit_params)
    return grid.best_estimator_, grid.best_params_, grid.cv_results_

