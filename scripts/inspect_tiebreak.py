import pandas as pd
p='data/charting-m-points-2020s.csv'
df=pd.read_csv(p, low_memory=False)
mask = df['TbSet'].notna()
if not mask.any():
    print('No TbSet rows')
else:
    match_id = df[mask]['match_id'].iloc[0]
    mdf = df[df['match_id']==match_id]
    print('match_id', match_id)
    print(mdf[['Pt','Set1','Set2','Gm1','Gm2','Pts','TbSet','PtWinner']].head(30).to_string(index=False))
    print('---- around tiebreak rows ----')
    tb_rows = mdf[(mdf['Gm1']==6)&(mdf['Gm2']==6)]
    if not tb_rows.empty:
        for idx in tb_rows.index[:5]:
            i = idx
            a = mdf.loc[max(mdf.index.min(), i-3):i+3, ['Pt','Set1','Set2','Gm1','Gm2','Pts','TbSet','PtWinner']]
            print(a.to_string())
            break
