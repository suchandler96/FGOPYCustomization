class Summer890PPTurn(Turn):
    def __init__(self):
        super(Summer890PPTurn, self).__init__()
    def __call__(self,turn):
        self.stage,self.stageTurn=[t:=Detect(.2).getStage(),1+self.stageTurn*(self.stage==t)]
        if turn==1:
            Detect.cache.setupServantDead()
            self.stageTotal=Detect.cache.getStageTotal()
            self.servant=[(lambda x:(x,)+servantData.get(x,(0,0,0,0,(0,0),((0,0),(0,0),(0,0)))))(Detect.cache.getFieldServant(i))for i in range(3)]
        else:
            for i in(i for i in range(3)if Detect.cache.isServantDead(i)):
                self.servant[i]=(lambda x:(x,)+servantData.get(x,(0,0,0,0,(0,0),((0,0),(0,0),(0,0)))))(Detect.cache.getFieldServant(i))
                self.countDown[0][i]=[0,0,0]
        logger.info(f'Turn {turn} Stage {self.stage} StageTurn {self.stageTurn} {[i[0]for i in self.servant]}')
        if self.stageTurn==1:Detect.cache.setupEnemyGird()
        self.enemy=[Detect.cache.getEnemyHp(i)for i in range(6)]

        # dispatch skill and select card
        if self.stage == 1:
            if self.stageTurn == 1:
                self.castSingleOrNoTargetServantSkill(2, 0, 1)      # 梅莉1技能给2号位汇呆
                self.castSingleOrNoTargetServantSkill(2, 1, 9)      # 梅莉2技能
                self.castMasterSkill(2, [2, 3])                         # 御主技能换人，3号位梅莉换C呆
                self.castSingleOrNoTargetServantSkill(0, 0, 9)      # 水摩根1技能
                self.castSingleOrNoTargetServantSkill(0, 1, 9)      # 水摩根2技能
                self.castSingleOrNoTargetServantSkill(1, 1, 0)      # 汇呆2技能给1号位水摩根
                self.castMasterSkill(0,)                                            # 御主礼装加攻击

                fgoDevice.device.perform(' ',(2100,))
                fgoDevice.device.perform(self.selectCard_s1_st1(),(300,300,2300,1300,6000))
            else:
                fgoDevice.device.perform(' ',(2100,))
                fgoDevice.device.perform(self.selectCard_s1_st2(),(300,300,2300,1300,6000))
        elif self.stage == 2:
            if self.stageTurn == 1:
                self.castSingleOrNoTargetServantSkill(0, 2, 0)
                self.castSingleOrNoTargetServantSkill(2, 0, 0)
                self.castSingleOrNoTargetServantSkill(2, 2, 1)
                self.castSingleOrNoTargetServantSkill(1, 2, 0)

                fgoDevice.device.perform(' ',(2100,))
                fgoDevice.device.perform(self.selectCard_s2_st1(),(300,300,2300,1300,6000))
            else:
                fgoDevice.device.perform(' ',(2100,))
                fgoDevice.device.perform(self.selectCard(),(300,300,2300,1300,6000))
        else:
            if self.stageTurn == 1:
                self.castSingleOrNoTargetServantSkill(2, 1, 1)
                self.castSingleOrNoTargetServantSkill(1, 0, 0)

                fgoDevice.device.perform(' ',(2100,))
                fgoDevice.device.perform(self.selectCard_s3_st1(),(300,300,2300,1300,6000))
            else:
                fgoDevice.device.perform(' ',(2100,))
                fgoDevice.device.perform(self.selectCard(),(300,300,2300,1300,6000))

    def castSingleOrNoTargetServantSkill(self,pos,skill,target):
        fgoDevice.device.press(('ASD','FGH','JKL')[pos][skill])
        if Detect(.7).isSkillNone():
            logger.warning(f'Skill {pos} {skill} Disabled')
            self.countDown[0][pos][skill]=999
            fgoDevice.device.press('\x08')
        elif Detect.cache.isSkillCastFailed():
            logger.warning(f'Skill {pos} {skill} Cast Failed')
            self.countDown[0][pos][skill]=1
            fgoDevice.device.press('J')
        elif t:=Detect.cache.getSkillTargetCount():fgoDevice.device.perform('234'[target]+'\x08',(300,700))
        else:fgoDevice.device.perform('\x08',(700,))
        while not Detect().isTurnBegin():pass
        Detect(.5)

    # targets expect a list, even when the master skill applies to a single servant
    # do not consider master skills that apply to enemies currently
    def castMasterSkill(self, skill, targets=[0, 3]):
        if skill == 2:
            if len(targets) != 2: return   # todo: currently only accept certain master reisou
        self.countDown[1][skill]=15
        fgoDevice.device.perform('Q'+'WER'[skill],(300,300))
        if len(targets) == 2:
            fgoDevice.device.perform(('TYUIOP'[targets[0]],'TYUIOP'[targets[1]],'Z'),(300,300,2600))
            fgoDevice.device.perform('\x08',(2300,))
            while not Detect().isTurnBegin():pass
        elif len(targets) == 1:
            if targets[0] >= 3: return
            if not Detect.cache.isServantDead(targets[0]):
                fgoDevice.device.perform(('TYUIOP'[targets[0]]),(2600,))

    @logit(logger,logging.INFO)
    def selectCard(self):
        color,sealed,hougu,np,resist,critical,group=Detect().getCardColor()+[i[5][1]for i in self.servant],Detect.cache.isCardSealed(),Detect.cache.isHouguReady(),[Detect.cache.getFieldServantNp(i)<100 for i in range(3)],[[1,1.7,.6][i]for i in Detect.cache.getCardResist()],[i/10 for i in Detect.cache.getCardCriticalRate()],[next(j for j,k in enumerate(self.servant)if k[0]==i)for i in Detect.cache.getCardServant([i[0] for i in self.servant if i[0]])]+[0,1,2]
        houguTargeted,houguArea,houguSupport=[[j for j in range(3)if hougu[j]and self.servant[j][0]and self.servant[j][5][0]==i]for i in range(3)]
        houguArea=houguArea if self.stage==self.stageTotal or sum(i>0 for i in self.enemy)>1 and sum(self.enemy)>12000 else[]
        houguTargeted=houguTargeted if self.stage==self.stageTotal or max(self.enemy)>23000+8000*len(houguArea)else[]
        hougu=[i+5 for i in houguSupport+houguArea+houguTargeted]
        if self.stageTurn==1 or houguTargeted or self.enemy[self.target]==0:
            self.target=numpy.argmax(self.enemy)
            fgoDevice.device.perform('\x67\x68\x69\x64\x65\x66'[self.target],(500,))
        self.enemy=[max(0,i-18000*len(houguArea))for i in self.enemy]
        if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])
        for _ in houguTargeted:
            self.enemy[self.target]=max(0,self.enemy[self.target]-48000)
            if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])
        def evaluate(card):return(lambda chainError:(lambda colorChain:(lambda firstBonus:
            sum(
                ((.3*bool(firstBonus&4)+.1*bool(firstBonus&1)+[1.,1.2,1.4][i]*[1,.8,1.1][color[j]])*(1+min(1,critical[j]+.2*bool(firstBonus&2)))+bool(colorChain==2))*resist[j]*(not sealed[j])
                for i,j in enumerate(card)if j<5
            )
            +4*(len([i for i in self.enemy if i])>1)*(self.enemy[self.target]<20000)*sum(bool(i)for i in numpy.diff([group[i]for i in card if i<5]))
            +(1.8 if colorChain==-1 else 3)*(not chainError and len({group[i]for i in card})==1)*resist[card[0]]
            +2.3*(colorChain==0)*len({group[i]for i in card if i<5 and np[group[i]]})
            +3*(colorChain==1)
            )(7 if colorChain==3 else 1<<color[0]))(-1 if chainError else{(0,):0,(1):1,(2,):2,(0,1,2):3}.get(tuple(set(color[i]for i in card)),-1)))(any(sealed[i]for i in card if i<5))
        card=list(max(permutations(range(5),3-len(hougu)),key=lambda x:evaluate(hougu+list(x))))
        return''.join(['12345678'[i]for i in hougu+card+list({0,1,2,3,4}-set(card))])

    @logit(logger,logging.INFO)
    def selectCard_s1_st1(self):
        color,sealed,hougu,np,resist,critical,group=Detect().getCardColor()+[i[5][1]for i in self.servant],Detect.cache.isCardSealed(),Detect.cache.isHouguReady(),[Detect.cache.getFieldServantNp(i)<100 for i in range(3)],[[1,1.7,.6][i]for i in Detect.cache.getCardResist()],[i/10 for i in Detect.cache.getCardCriticalRate()],[next(j for j,k in enumerate(self.servant)if k[0]==i)for i in Detect.cache.getCardServant([i[0] for i in self.servant if i[0]])]+[0,1,2]
        houguTargeted,houguArea,houguSupport=[[j for j in range(3)if hougu[j]and self.servant[j][0]and self.servant[j][5][0]==i]for i in range(3)]
        houguArea=houguArea if self.stage==self.stageTotal or sum(i>0 for i in self.enemy)>1 and sum(self.enemy)>12000 else[]
        houguTargeted=houguTargeted if self.stage==self.stageTotal or max(self.enemy)>23000+8000*len(houguArea)else[]

        if self.stageTurn==1 or houguTargeted or self.enemy[self.target]==0:
            self.target=numpy.argmax(self.enemy)
            fgoDevice.device.perform('\x67\x68\x69\x64\x65\x66'[self.target],(500,))
        self.enemy=[max(0,i-18000*len(houguArea))for i in self.enemy]
        if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])
        for _ in houguTargeted:
            self.enemy[self.target]=max(0,self.enemy[self.target]-48000)
            if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])
        def evaluate(card):
            # 0: Represents the "Arts" card color.
            # 1: Represents the "Quick" card color.
            # 2: Represents the "Buster" card color.
            mark = 0.
            if group[card[0]] != group[card[1]]:
                mark += 1
            if color[card[0]] == 2:
                mark *= 2
            if color[card[1]] == 2:
                mark *= 2
            return mark
        card=list(max(permutations(range(5),3-1),key=lambda x:evaluate(list(x))))
        return''.join(['12345678'[i]for i in [5]+card+list({0,1,2,3,4}-set(card))])

    @logit(logger,logging.INFO)
    def selectCard_s1_st2(self):
        color,sealed,hougu,np,resist,critical,group=Detect().getCardColor()+[i[5][1]for i in self.servant],Detect.cache.isCardSealed(),Detect.cache.isHouguReady(),[Detect.cache.getFieldServantNp(i)<100 for i in range(3)],[[1,1.7,.6][i]for i in Detect.cache.getCardResist()],[i/10 for i in Detect.cache.getCardCriticalRate()],[next(j for j,k in enumerate(self.servant)if k[0]==i)for i in Detect.cache.getCardServant([i[0] for i in self.servant if i[0]])]+[0,1,2]
        houguTargeted,houguArea,houguSupport=[[j for j in range(3)if hougu[j]and self.servant[j][0]and self.servant[j][5][0]==i]for i in range(3)]
        houguArea=houguArea if self.stage==self.stageTotal or sum(i>0 for i in self.enemy)>1 and sum(self.enemy)>12000 else[]
        houguTargeted=houguTargeted if self.stage==self.stageTotal or max(self.enemy)>23000+8000*len(houguArea)else[]
        if self.stageTurn==1 or houguTargeted or self.enemy[self.target]==0:
            self.target=numpy.argmax(self.enemy)
            fgoDevice.device.perform('\x67\x68\x69\x64\x65\x66'[self.target],(500,))
        self.enemy=[max(0,i-18000*len(houguArea))for i in self.enemy]
        if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])
        for _ in houguTargeted:
            self.enemy[self.target]=max(0,self.enemy[self.target]-48000)
            if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])

        def evaluate(card):
            # 0: Represents the "Arts" card color.
            # 1: Represents the "Quick" card color.
            # 2: Represents the "Buster" card color.
            mark = 0.
            if group[card[0]] != group[card[1]]:
                mark += 1
            if group[card[1]] != group[card[2]]:
                mark += 1
            if color[card[0]] == 0:
                mark *= 2
            return mark

        card=list(max(permutations(range(5),3),key=lambda x:evaluate(list(x))))
        return''.join(['12345678'[i]for i in card+list({0,1,2,3,4}-set(card))])

    @logit(logger,logging.INFO)
    def selectCard_s2_st1(self):
        return''.join(['12345678'[i]for i in [7,6,0]])

    @logit(logger,logging.INFO)
    def selectCard_s3_st1(self):
        group=[next(j for j,k in enumerate(self.servant)if k[0]==i)for i in Detect.cache.getCardServant([i[0] for i in self.servant if i[0]])]+[0,1,2]

        def evaluate(card):
            mark = 0.
            if group[card[0]] == 1:
                mark += 1
            return mark
        card=list(max([[0],[1],[2],[3],[4]],key=lambda x:evaluate(x)))
        return''.join(['12345678'[i]for i in [5,6] + card])




