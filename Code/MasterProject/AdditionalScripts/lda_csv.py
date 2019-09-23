import sys

def create_ldatopics_sql(theta_file, out_path, thre=0.08):
    a=[]
    index=0
    id=1
    print('starting insertion')
    with open(out_path+'lda_theta_db.csv','w') as sql:
        sql.write('"id";"topic_id";"value";"paper_id";"doc_id"\n')
        with open(theta_file) as f:
            for line in f:
                #paper_obj=model.PaperMapping.objects.get(doc_id=index)
                paper_dis = [float(x) for x in line.replace("\n", "").split(' ') if x != ""]
                
                for i, value in enumerate(paper_dis):
                    '''model.PaperLDATheta.objects.create(paper_id=index+1,
                                                       doc_id=index,
                                                       topic_id=i,
                                                       value=value)'''
                    if value>float(thre):
                        sql.write('{};{};{};{};{}\n'.format(id,i,value,index+1,index))
                        id=id+1
                index=index+1
                #print('paper id {}, doc id {} inserted'.format(index+1, index))
    print('insertion completed')
    return

if __name__ == "__main__":
   create_ldatopics_sql(sys.argv[1],sys.argv[2])
